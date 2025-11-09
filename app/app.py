# app/app.py
import os
import json
from typing import List, Dict, Any
import streamlit as st
import PyPDF2 as pdf
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
from streamlit.components.v1 import html as components_html   # for confetti hearts

# ------------------------------
# Page & theme
# ------------------------------
load_dotenv()
st.set_page_config(page_title="For You ♡", page_icon="💌", layout="wide")

# Romantic CSS (fonts, cards, buttons, background)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Great+Vibes&family=Playfair+Display:wght@500;700&family=Inter:wght@400;600&display=swap');

html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }

.romantic-title {
  font-family: 'Great Vibes', cursive !important;
  font-size: 64px !important;
  color: #B5838D !important;
  text-align: center;
  margin: 0.2rem 0 0.2rem 0;
}

.tagline {
  text-align:center; color:#7A5C65; margin-top:-8px; margin-bottom:18px;
}

.love-banner{
  background:#FFF6F9;
  border:1px solid rgba(181,131,141,.25);
  color:#5A4B52;
  border-radius:14px;
  padding:12px 16px;
  text-align:center;
  margin: 4px 0 18px 0;
  box-shadow: 0 2px 10px rgba(181,131,141,0.08);
}
.love-banner b{ color:#7A5C65; }

.heart-card {
  background: linear-gradient(180deg, #FEF1F5 0%, #FDE2E4 100%);
  border-radius: 20px;
  padding: 22px 24px;
  box-shadow: 0 8px 24px rgba(181,131,141,0.18);
  border: 1px solid rgba(181,131,141,0.22);
  margin-bottom: 18px;
}

.ribbon {
  height: 1px; width: 100%;
  background: linear-gradient(90deg, rgba(0,0,0,0), #D9ABDA, rgba(0,0,0,0));
  margin: 16px 0 12px 0;
}

section[data-testid="stSidebar"] button, .stButton>button {
  border-radius: 999px;
  padding: 0.6rem 1.2rem;
  font-weight: 600;
}

.heart-list li::marker { content: "❤  "; color:#B5838D; }

body:before {
  content:"";
  position: fixed; inset:0;
  background:
    radial-gradient( circle at 10% 10%, rgba(245,214,220,0.35) 0 120px, transparent 130px),
    radial-gradient( circle at 90% 20%, rgba(217,171,218,0.30) 0 120px, transparent 130px),
    radial-gradient( circle at 15% 85%, rgba(250,218,221,0.35) 0 120px, transparent 130px);
  pointer-events:none; z-index:-1;
}
table { border-radius:14px; overflow:hidden; }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# HF Client
# ------------------------------
HF_TOKEN = os.getenv("HF_TOKEN") or st.secrets.get("HF_TOKEN")
if not HF_TOKEN:
    st.error("HF_TOKEN missing in .env file")
client = InferenceClient(api_key=HF_TOKEN)

# ------------------------------
# Small UI helpers
# ------------------------------
def card(title: str, body_md: str):
    st.markdown(f'''
    <div class="heart-card">
      <h3 style="margin:0;color:#7A5C65">{title}</h3>
      <div class="ribbon"></div>
      <div>{body_md}</div>
    </div>
    ''', unsafe_allow_html=True)

def heart_confetti():
    components_html("""
    <script>
      const burst = () => {
        const colors = ['#B5838D','#D9ABDA','#FADADD','#FDE2E4'];
        for (let i=0;i<28;i++){
          const e = document.createElement('div');
          e.innerHTML = '❤';
          e.style.position='fixed';
          e.style.left = (50 + (Math.random()*24-12)) + 'vw';
          e.style.top = (18 + (Math.random()*10-5)) + 'vh';
          e.style.fontSize = (18+Math.random()*18)+'px';
          e.style.color = colors[Math.floor(Math.random()*colors.length)];
          e.style.opacity = 1;
          e.style.transition = 'transform 1.6s ease-out, opacity 1.6s ease-out';
          e.style.zIndex = 9999;
          document.body.appendChild(e);
          const x = (Math.random()*2-1)*180;
          const y = 240 + Math.random()*150;
          requestAnimationFrame(()=> {
            e.style.transform = `translate(${x}px, ${y}px) rotate(${Math.random()*120-60}deg)`;
            e.style.opacity = 0;
          });
          setTimeout(()=> e.remove(), 1700);
        }
      };
      burst();
    </script>
    """, height=0)

# ------------------------------
# Core logic
# ------------------------------
def input_pdf_text(uploaded_file) -> str:
    reader = pdf.PdfReader(uploaded_file)
    out = []
    for page in reader.pages:
        out.append(page.extract_text() or "")
    return "\n".join(out)

def ats_companywise_prompt(resume_text: str, jd_text: str) -> List[Dict[str, str]]:
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

Evaluation Bands:
- 90–100 Excellent
- 75–89 Good
- 50–74 Average
- <50 Poor

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

def call_deepseek(resume_text: str, jd_text: str) -> Dict[str, Any]:
    messages = ats_companywise_prompt(resume_text, jd_text)
    completion = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3.2-Exp",
        messages=messages,
        temperature=0.0,
        max_tokens=4000,
    )
    content = completion.choices[0].message["content"]
    text = content if isinstance(content, str) else json.dumps(content)
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("` \n\r\t")
        if t.lower().startswith("json"):
            t = t[4:].strip()
    try:
        return json.loads(t)
    except Exception:
        return {"raw_output": t}

# ------------------------------
# Header + fixed gift banner
# ------------------------------
st.markdown('<div class="romantic-title" title="thank you for being you">A Little Resume Magic, For You ♡</div>', unsafe_allow_html=True)
st.markdown('<div class="tagline">curated suggestions tailored to your journey — with love</div>', unsafe_allow_html=True)

# Fixed message for Shaive (no input box)
SHAIVE_NAME = "Shaive"
LOVE_NOTE = "Every step you’ve taken is beautiful. Let’s polish it together."
st.markdown(f'<div class="love-banner"><b>{SHAIVE_NAME}</b>, {LOVE_NOTE}</div>', unsafe_allow_html=True)

# ------------------------------
# Inputs
# ------------------------------
jd = st.text_area("Paste the Job Description")
uploaded_file = st.file_uploader("Upload Your Resume (PDF)", type="pdf", help="Upload a PDF resume")

# Romantic CTA
submit_col, _ = st.columns([1,3])
with submit_col:
    submit = st.button("Shall we polish this together? ❤", use_container_width=True)

# ------------------------------
# Run
# ------------------------------
if submit:
    if not uploaded_file:
        st.error("Please upload a PDF file first.")
    elif not jd.strip():
        st.error("Please paste a job description.")
    else:
        # Cute spinner text instead of "Analyzing with DeepSeek..."
        with st.spinner("Sprinkling a little stardust on your resume… ✨"):
            resume_text = input_pdf_text(uploaded_file)
            result = call_deepseek(resume_text, jd)

        if "raw_output" in result:
            st.error("Model did not return valid JSON. Showing raw output below.")
            st.code(result["raw_output"])
            st.stop()

        # Celebrate!
        heart_confetti()

        # ---- Score card
        total_score = result.get('total_score', '—')
        percentage_match = result.get('percentage_match', '—')
        section_scores = result.get("section_scores") or {}
        sec_lines = []
        for label in ["address", "about", "skills", "experience", "github", "medium", "resume_name"]:
            if label in section_scores:
                sec_lines.append(f"- **{label.capitalize()}**: {section_scores[label]}")
        card("Your Score & Match",
             f"- **Total:** **{total_score} / 100**  \n"
             f"- **JD Match:** **{percentage_match}%**  \n\n" +
             ("\n".join(sec_lines) if sec_lines else "")
        )

        # ---- Suggestions
        suggestions = result.get("suggestions") or []
        card("Sweet Suggestions",
             "<ul class='heart-list'>" + "".join([f"<li>{s}</li>" for s in suggestions]) + "</ul>" if suggestions else "—")

        # ---- Missing keywords
        miss = result.get("missing_keywords") or []
        card("Missing Keywords (to weave in)", ", ".join(miss) if miss else "All set!")

        # ---- About preview
        about = result.get("about") or {}
        about_body = []
        if about:
            about_body.append(f"**Present:** {about.get('present')}")
            about_body.append(f"**Recommended Header:** {about.get('recommended_header')}")
            if about.get("preview"):
                about_body.append(f"> {about.get('preview')}")
        card("About Section (Preview)", "<br/>".join(about_body) if about_body else "—")

        # ---- Skills
        skills = result.get("skills_list") or []
        card("Normalized Skills", ", ".join(skills) if skills else "—")

        # ---- Links & resume name
        g = result.get("github_links") or []
        m = result.get("medium_links") or []
        rn = result.get("resume_name_recommendation")
        links_body = []
        if g: links_body.append("**GitHub:** " + ", ".join(g))
        if m: links_body.append("**Medium:** " + ", ".join(m))
        if rn: links_body.append("**Resume Name Recommendation:** " + rn)
        card("Links & Name", "<br/>".join(links_body) if links_body else "—")

        # ---- Company-wise rewrites
        exp = result.get("experience_company_analysis") or []
        if not exp:
            card("Expert Suggestions — Company-wise Bullet Rewrites", "_No experience entries parsed._")
        else:
            for entry in exp:
                company = entry.get("company") or "(Company)"
                role = entry.get("role") or ""
                dates = entry.get("dates") or ""
                header = f"**{company}**"
                if role or dates:
                    header += f" &nbsp;&nbsp; <span style='color:#7A5C65'>({role} — {dates})</span>"
                body = []
                if entry.get("summary"):
                    body.append(entry["summary"])
                bullets = entry.get("bullets") or []
                if bullets:
                    for idx, b in enumerate(bullets, start=1):
                        issues = "; ".join(b.get("issues") or [])
                        star = "; ".join(b.get("star_violations") or [])
                        tags = ", ".join(b.get("jd_alignment") or [])
                        score = b.get("impact_score", "—")
                        body.append(
                            f"<div class='ribbon'></div>"
                            f"<b>Bullet {idx}</b><br/>"
                            f"- <i>Original</i>: {b.get('original','')}<br/>"
                            f"- <i>Rewrite</i>: {b.get('rewrite','')}<br/>"
                            + (f"- <i>Issues</i>: {issues}<br/>" if issues else "")
                            + (f"- <i>STAR Violations</i>: {star}<br/>" if star else "")
                            + (f"- <i>JD Alignment Tags</i>: {tags}<br/>" if tags else "")
                            + f"- <i>Impact Score</i>: {score}/100"
                        )
                else:
                    body.append("_No bullets detected._")
                card(header, "<br/>".join(body))

        # ---- Debug JSON
        with st.expander("Raw JSON (debug)"):
            st.json(result)
