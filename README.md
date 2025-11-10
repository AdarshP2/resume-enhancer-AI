**🧭 Resume Evaluator**

ATS-Style Resume Analysis with JD Alignment and STAR Bullet Rewrites

**🌟 Overview**

Resume Evaluator is a modern Streamlit web app that analyzes resumes against job descriptions using an advanced LLM (DeepSeek-V3.2).
It evaluates ATS scores, JD keyword alignment, and rewrites bullet points into STAR-compliant, measurable statements — all inside a clean, glass-style UI.

**✨ Features**

📄 PDF Resume Upload

💼 JD Text Matching (Smart context-aware comparison)

🧠 AI-Driven Resume Scoring

Address / About / Skills / Experience / GitHub / Medium / Resume Naming

🧩 STAR-Based Bullet Rewrites

Detects weak verbs and rewrites for impact

🧾 ATS-Friendly Keyword Extraction

🎨 Dynamic Streamlit UI

Gradient header

Glass cards & badges

Interactive tabs for results

**⚡ Runs locally or online (Streamlit Cloud, Hugging Face Spaces, etc.)**

**🧰 Tech Stack**
Layer	Technology
Frontend	Streamlit (Custom CSS for dynamic UI)
Backend	Python 3.10+, Hugging Face Inference API
LLM	DeepSeek-V3.2-Exp
PDF Processing	PyPDF2
Environment Handling	python-dotenv
**🧑‍💻 Setup Instructions**
**1️⃣ Clone the Repository**
git clone https://github.com/<your-username>/resume-evaluator.git
cd resume-evaluator

**2️⃣ Create Virtual Environment**
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

**3️⃣ Install Dependencies**
pip install -r requirements.txt

**4️⃣ Add Hugging Face Token**

Create a .env file in the root directory:

HF_TOKEN=your_huggingface_api_token


**You can generate one here → https://huggingface.co/settings/tokens**

**5️⃣ Run the App**
streamlit run app/app.py


**The app will open at**
👉 http://localhost:8501

**🎨 UI Highlights**
**Section	Description**
Hero Header	Clean gradient banner introducing the app
Upload Panel	Drag-and-drop resume upload + JD text area with character counter
Tabs Layout	Dynamic result sections: Overview / Suggestions / Keywords / About / Skills / Company Rewrites
Glass Cards	Each section wrapped in translucent cards for readability
Badges & Pills	Keywords and metrics styled for visual clarity
**🧾 Output Structure (from LLM)**

The app expects and parses JSON like:

{
  "percentage_match": 84,
  "total_score": 91,
  "section_scores": {
    "address": 9,
    "about": 10,
    "skills": 18,
    "experience": 28,
    "github": 10,
    "medium": 6,
    "resume_name": 10
  },
  "missing_keywords": ["automation", "leadership", "KPI"],
  "suggestions": ["Add metrics to your impact statements", "Include a summary header"],
  "experience_company_analysis": [
    {
      "company": "ABC Corp",
      "role": "QA Engineer",
      "dates": "2021–2023",
      "bullets": [
        {
          "original": "Worked on test automation scripts",
          "rewrite": "Developed and deployed automated test scripts improving test efficiency by 35%",
          "impact_score": 87
        }
      ]
    }
  ]
}

**🚀 Deployment Options**

You can deploy this app for free on:

Streamlit Cloud
→ https://streamlit.io/cloud

Hugging Face Spaces
→ Supports requirements.txt + app.py

Render / Vercel / Railway
→ Simple Python + Streamlit Docker deployment

**📁 Project Structure**
resume-evaluator/
│
├── app/
│   ├── app.py                # Main Streamlit application
│   └── logic/                # Optional logic modules
│
├── .streamlit/
│   └── config.toml           # Theme configuration
│
├── requirements.txt
├── .env                      # (not committed) Hugging Face token
└── README.md


**🪄 Future Enhancements**

 Add resume PDF download with improved rewrites

 Support for multiple JDs comparison

 Integration with LinkedIn profile parser

 Multilingual support

**🧡 Credits**

Developed with 💻 + ☕ using
Python · Streamlit · Hugging Face · DeepSeek

**📜 License**

This project is licensed under the MIT License — you’re free to use, modify, and share it.
