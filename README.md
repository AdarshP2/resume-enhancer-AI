# 🧭 Resume Evaluator

**ATS-Style Resume Analysis with Job Description Alignment and STAR Bullet Rewrites**

---

## Overview

**Resume Evaluator** is a modern Streamlit web app that analyzes resumes against job descriptions using an advanced LLM (**DeepSeek-V3.2**).  
It evaluates ATS compatibility, keyword alignment, and rewrites experience bullets into **STAR-compliant, measurable statements** — all within a clean, glass-style user interface.

---

## Features

| Category | Description |
|-----------|--------------|
| **PDF Resume Upload** | Upload any resume in PDF format for AI analysis. |
| **JD Text Matching** | Smart, context-aware comparison with job descriptions. |
| **AI-Driven Resume Scoring** | Section-wise ATS scoring for address, skills, experience, etc. |
| **STAR-Based Bullet Rewrites** | Converts weak action points into measurable, impact-driven statements. |
| **ATS Keyword Extraction** | Identifies missing and existing keywords to boost visibility. |
| **Dynamic Streamlit UI** | Gradient header, glass cards, interactive tabs, and clean typography. |

---

## Demo

**Live App:** [Resume Evaluator on Streamlit Cloud](https://resume-enhancer-ai-general.streamlit.app/)

---

## Tech Stack

| Layer | Technology |
|--------|-------------|
| **Frontend** | Streamlit (Custom CSS for dynamic UI) |
| **Backend** | Python 3.10+, Hugging Face Inference API |
| **LLM** | DeepSeek-V3.2-Exp |
| **PDF Processing** | PyPDF2 |
| **Environment Handling** | python-dotenv |

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/resume-evaluator.git
cd resume-evaluator
