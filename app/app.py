# app/app.py
import os
import json
from typing import List, Dict, Any

import streamlit as st
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
import PyPDF2 as pdf


# ------------------------------
# Page & theme
# ------------------------------
load_dotenv()
st.set_page_config(
    page_title="Resume Evaluator",
    page_icon="🧭",
    layout="wide",
)

# Global CSS (modern, neutral, glassy)
st.markdown("""
<style>
:root {
  --card-bg: rgba(255,255,255,0.7);
  --card-border: rgba(0,0,0,0.06);
  --shadow-sm: 0 6px 16px rgba(0,0,0,0.06);
  --shadow-md: 0 12px 28px rgba(0,0,0,0.08);
  --brand: #2B6CB0; /* sync with theme primaryColor */
  --muted: #4A5568; /* slate */
}

html, body, [class*="css"]  {
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial, "Noto Sans";
}

/* Hero section */
.hero {
  border-radius: 18px;
  padding: 26px 28px;
  background: linear-gradient(135deg, #EBF4FF 0%, #F7FAFC 55%, #FFFFFF 100%);
  border: 1px solid rgba(0,0,0,0.06);
  box-shadow: var(--shadow-md);
  margin-bottom: 10px;
}
.hero h1 {
  margin: 0 0 8px 0;
  font-size: 34px;
  letter-spacing: .2px;
}
.hero p {
  margin: 0; color: var(--muted);
}

/* Glass cards */
.card {
  background: var(--card-bg);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid var(--card-border);
  border-radius: 16px;
  padding: 18px 20px;
  box-shadow: var(--shadow-sm);
  margin-bottom: 16px;
}

/* Section headings inside cards */
.card h3 {
  margin: 0 0 8px 0;
  font-weight: 700;
}
.ribbon {
  height: 1px; width: 100%;
  background: linear-gradient(90deg, rgba(0,0,0,0), #E2E8F0, rgba(0,0,0,0));
  margin: 10px 0 12px 0;
}

/* Primary button styling */
.stButton>button {
  border-radius: 12px !important;
  padding: 0.8rem 1.1rem !important;
  font-weight: 700 !important;
  transition: transform .05s ease, box-shadow .15s ease !important;
  box-shadow: 0 8px 20px rgba(43,108,176,0.18) !important;
}
.stButton>button:hover { transform: translateY(-1px); }

/* Pills / badges */
.pill {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  background: #EDF2F7;
  border: 1px solid #E2E8F0;
  color: #2D3748;
  font-size: 12px;
  margin-right: 8px;
}

/* Lists */
ul.clean { padding-left: 1.1rem; margin: 0; }
ul.clean li { margin: 6px 0; }

/* Hide Streamlit's deploy/help menu dots for cleaner look (still clickable via hotkeys) */
header [data-testid="stMainMenu"] { opacity: .65; }
</style>
""", unsafe_allow_html=True)


# ------------------------------
# Hugging Face client (no UI disclosure)
# ------------------------------
HF_TOKEN = os.getenv("HF_TOKEN") or st.secrets.get("HF_TOKEN")
client = InferenceClient(api_key=HF_TOKEN) if HF_TOKEN else None


# ------------------------------
# Helpers
# ------------------------------
def card(title: str, body_md: str = ""):
    st.markdown(f"""
    <div class="card">
      <h3>{title}</h3>
      <div class="ribbon"></div>
      <div>{body_md}</div>
    </div>
    """, unsafe_allow_html=True)


def pdf_to_text(file) -> str:
    reader = pdf.PdfReader(file)
    out = []
    for page in reader.pages:
        out.append(page.extract_text() or "")
    return "\n".join(out)


def build_prompt(resume_text: str, jd_text: str) -> list[dict[str, str]]:
    rubric = r"""
Act as a Resume Checker and ATS. You will:
1) Score the resume using the rubric below (on ORIGINAL content only).
2) Extract each EXPERIENCE entry grouped by company (company, role, dates, bullets).
3) For EACH bullet, analyze problems, STAR compliance, and alignment to the Job Description (JD).
4) Rewrite each bullet to be STAR-compliant, action-led, and JD-aligned with a measurable outcome.
5) Explain the rationale and list JD keywords used.

Rubric (Total 100):
- Address: 10 (5 address, 3 phone, 2 email)
- About: 10 (5 presence, 5 quality; if missing => 0)
- Skills: 20 (correctly identified and formatted skills)
- Experience: 30 (15 STAR compliance; 10 focus/impact; 5 order/links)
  - Deduct 2 points for each bullet missing quantitative value
- GitHub + Medium: 20 (10 each)
- Resume Name: 10

Evaluation Bands: 90–100 Excellent, 75–89 Good, 50–74 Average, <50 Poor

STRICT INSTRUCTIONS:
- Calculate ALL scores on ORIGINAL content (not your rewrites).
- For STAR, traverse ALL bullets/sentences; deduct points strictly when violated.
- Use concise, high-signal text.
- Do NOT add extra keys beyond the schema.

Return ONLY a JSON object with EXACTLY this schema:

{
  "percentage_match": number,
  "total_score": number,
  "section_scores": {
    "address": number, "about": number, "skills": number,
    "experience": number, "github": number, "medium": number, "resume_name": number
  },
  "missing_keywords": [ "string", ... ],
  "suggestions": [ "string", ... ],
  "about": { "present": boolean, "recommended_header": "About" | "No Change", "preview": "string" },
  "skills_list": [ "string", ... ],
  "github_links": [ "string", ... ],
  "medium_links": [ "string", ... ],
  "resume_name_recommendation": "string",
  "experience_company_analysis": [
    {
      "company": "string", "role": "string", "dates": "string",
      "bullets": [
        {
          "original": "string",
          "issues": [ "string", ... ],
          "star_violations": [ "string", ... ],
          "jd_alignment": [ "string", ... ],
          "rewrite": "string",
          "impact_score": number
        }
      ],
      "summary": "string"
    }
  ]
}
"""
    user = f"RESUME TEXT:\n{resume_text}\n\nJOB DESCRIPTION:\n{jd_text}\n\nRespond with ONLY the JSON object."
    return [
        {"role": "system", "content": rubric},
        {"role": "user", "content": user},
    ]


def parse_jsonish(text: str) -> Dict[str, Any]:
    s = (text or "").strip()
    if s.startswith("```"):
        s = s.strip("` \n\r\t")
        if s.lower().startswith("json"):
            s = s[4:].strip()
    try:
        return json.loads(s)
    except Exception:
        return {"raw_output": text}


def run_model(resume_text: str, jd_text: str) -> Dict[str, Any]:
    if not client:
        return {"error": "HF client not available (missing token)."}
    messages = build_prompt(resume_text, jd_text)
    completion = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3.2-Exp",
        messages=messages,
        temperature=0.0,
        max_tokens=4000,
    )
    content = completion.choices[0].message["content"]
    text = content if isinstance(content, str) else json.dumps(content)
    return parse_jsonish(text)


# ------------------------------
# Hero
# ------------------------------
st.markdown("""
<div class="hero">
  <h1>Resume Evaluator</h1>
  <p>ATS-style scoring, JD alignment, and STAR rewrites — clear, fast, and organized.</p>
</div>
""", unsafe_allow_html=True)


# ------------------------------
# Input row
# ------------------------------
left, right = st.columns([1, 1])

with left:
    uploaded = st.file_uploader("Upload resume (PDF)", type=["pdf"])
    if uploaded is not None:
        size_kb = f"{(uploaded.size/1024):.0f} KB"
        st.markdown(f"<span class='pill'>📄 {uploaded.name}</span><span class='pill'>📦 {size_kb}</span>", unsafe_allow_html=True)

with right:
    jd_text = st.text_area("Paste the Job Description", height=180, placeholder="Paste the role’s JD here...")
    st.caption(f"Characters: {len(jd_text)}")

analyze = st.button("Analyze", type="primary", use_container_width=True)


# ------------------------------
# Run + Results
# ------------------------------
if analyze:
    if not uploaded:
        st.error("Please upload a PDF file.")
    elif not jd_text.strip():
        st.error("Please paste a Job Description.")
    else:
        with st.spinner("Evaluating…"):
            resume_text = pdf_to_text(uploaded)
            result = run_model(resume_text, jd_text)

        if result.get("error"):
            st.error(result["error"])
            st.stop()

        if "raw_output" in result:
            st.error("The model did not return valid JSON. Expand the Debug tab to see raw output.")
        
        # Tabs for a dynamic browsing experience
        tabs = st.tabs(["Overview", "Suggestions", "Keywords", "About", "Skills & Links", "Company Rewrites", "Debug"])

        # ---- Overview
        with tabs[0]:
            c1, c2, c3 = st.columns([1,1,1])
            total_score = result.get('total_score', None)
            pct_match = result.get('percentage_match', None)
            section_scores = result.get("section_scores") or {}

            with c1:
                card("Overall Score", f"<h2 style='margin:0'>{total_score if total_score is not None else '—'}/100</h2>")
            with c2:
                card("JD Match", f"<h2 style='margin:0'>{(str(pct_match) + '%') if pct_match is not None else '—'}</h2>")
            with c3:
                if section_scores:
                    lines = [f"- **{k.capitalize()}**: {v}" for k, v in section_scores.items()]
                    card("Section Scores", "<br/>".join(lines))
                else:
                    card("Section Scores", "—")

        # ---- Suggestions
        with tabs[1]:
            suggestions = result.get("suggestions") or []
            if suggestions:
                card("Actionable Suggestions",
                     "<ul class='clean'>" + "".join([f"<li>{s}</li>" for s in suggestions]) + "</ul>")
            else:
                card("Actionable Suggestions", "—")

        # ---- Keywords
        with tabs[2]:
            missing = result.get("missing_keywords") or []
            if missing:
                pills = " ".join([f"<span class='pill'>{kw}</span>" for kw in missing])
                card("Missing Keywords", pills)
            else:
                card("Missing Keywords", "None detected")

        # ---- About
        with tabs[3]:
            about = result.get("about") or {}
            body = []
            if about:
                body.append(f"**Present:** {about.get('present')}")
                if about.get("recommended_header"):
                    body.append(f"**Header:** {about.get('recommended_header')}")
                if about.get("preview"):
                    body.append(f"> {about.get('preview')}")
            card("About (detected)", "<br/>".join(body) if body else "—")

        # ---- Skills & Links
        with tabs[4]:
            s_left, s_right = st.columns([1,1])
            skills = result.get("skills_list") or []
            with s_left:
                card("Normalized Skills", ", ".join(skills) if skills else "—")

            links_body = []
            g = result.get("github_links") or []
            m = result.get("medium_links") or []
            rn = result.get("resume_name_recommendation")
            if g: links_body.append("**GitHub:** " + ", ".join(g))
            if m: links_body.append("**Medium:** " + ", ".join(m))
            if rn: links_body.append("**Resume Name Suggestion:** " + rn)
            with s_right:
                card("Links & Naming", "<br/>".join(links_body) if links_body else "—")

        # ---- Company Rewrites
        with tabs[5]:
            exp = result.get("experience_company_analysis") or []
            if not exp:
                card("Company-wise Bullet Rewrites", "_No experience entries parsed._")
            else:
                for entry in exp:
                    company = entry.get("company") or "(Company)"
                    role = entry.get("role") or ""
                    dates = entry.get("dates") or ""
                    header = f"**{company}**"
                    if role or dates:
                        header += f"  <span style='color:#7d8793'>({role} — {dates})</span>"

                    lines = []
                    if entry.get("summary"):
                        lines.append(entry["summary"])

                    bullets = entry.get("bullets") or []
                    if bullets:
                        for i, b in enumerate(bullets, start=1):
                            issues = "; ".join(b.get("issues") or [])
                            star = "; ".join(b.get("star_violations") or [])
                            tags = ", ".join(b.get("jd_alignment") or [])
                            score = b.get("impact_score", "—")

                            lines.append(
                                f"<div class='ribbon'></div>"
                                f"<b>Bullet {i}</b><br/>"
                                f"- <i>Original</i>: {b.get('original','')}<br/>"
                                f"- <i>Rewrite</i>: {b.get('rewrite','')}<br/>"
                                + (f"- <i>Issues</i>: {issues}<br/>" if issues else "")
                                + (f"- <i>STAR Violations</i>: {star}<br/>" if star else "")
                                + (f"- <i>JD Alignment</i>: {tags}<br/>" if tags else "")
                                + f"- <i>Impact Score</i>: {score}/100"
                            )
                    else:
                        lines.append("_No bullets detected._")

                    card(header, "<br/>".join(lines))

        # ---- Debug
        with tabs[6]:
            if "raw_output" in result:
                card("Raw Output", f"<pre style='white-space:pre-wrap'>{result['raw_output']}</pre>")
            else:
                st.json(result)
