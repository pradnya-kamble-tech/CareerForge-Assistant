⚡ CareerForge AI — AI-Powered Resume Intelligence System

An intelligent resume analysis platform that parses PDF resumes, extracts skills, scores them, predicts career paths, identifies skill gaps, and generates downloadable PDF reports.

🚀 Features

- **PDF Resume Parsing** — Upload a PDF and extract text automatically
- **Skill Mining** — Keyword-based skill detection across 8+ categories
- **Resume Scoring** — 0-100 scoring with explainable breakdown
- **Risk Analysis** — Resume risk assessment with actionable suggestions
- **Career Prediction** — Role matching with percentage-based predictions
- **Skill Gap Analysis** — Identify missing skills for your target role
- **Resume Evolution Simulator** — Digital twin to simulate skill additions
- **PDF Report Download** — Generate professional analysis reports
- **Authentication** — Login/Register with Student, Recruiter, Admin roles
- **Cloud Persistence** — Powered by Supabase PostgreSQL for permanent data storage

---

📁 Project Structure

```
careerforge/
├── app.py                 # Flask application (routes, auth, API)
├── database.py            # Dual-mode DB logic (SQLite/PostgreSQL)
├── analyzer.py            # AI logic (Skill extraction, scoring, risk)
├── resume_parser.py       # PDF text extraction
├── report_generator.py    # PDF report generation
├── render.yaml            # Render Blueprint deployment config
├── migrate_to_supabase.py # One-time cloud migration script
├── static/                # Styling & Javascript
└── templates/             # HTML Templates
```

---

## 🛠️ Local Setup

```bash
# 1. Clone / navigate to the project
cd careerforge

# 2. Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run (Defaults to SQLite if no DATABASE_URL set)
python app.py
```

---

## ☁️ Deployment (Supabase & Render)

### 1. Database Setup
1. Create a project on [Supabase](https://supabase.com).
2. Get your **Connection String (URI)** from Settings -> Database.

### 2. Deploy on Render
1. Push your code to GitHub.
2. Go to **Render Dashboard** -> **New** -> **Blueprint**.
3. Select this repository.
4. Set your Environment Variables:
   - `DATABASE_URL`: Your Supabase URI.
   - `ANTHROPIC_API_KEY`: Your Anthropic API key.
5. Click **Apply**.

---

## 📋 Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Flask (Python) |
| **Database** | PostgreSQL (Supabase) / SQLite |
| **Parsing** | pdfplumber |
| **Reports** | fpdf2 |
| **AI Support** | Anthropic Claude API |
| **Deployment**| Render / Gunicorn |

---

Built with ❤️ — **CareerForge AI**
