# InterviewX 🎯

> **Practice. Get Honest Feedback. Improve. Get Hired.**

An AI-powered interview preparation platform specifically engineered for students, fresh graduates, and tech job seekers preparing for campus placements (TCS, Infosys, Wipro, Capgemini) and high-scale product startup / Tier-1 technical interviews (Amazon, Google, Microsoft, Flipkart, Swiggy).

Unlike conventional mock interview platforms that provide flattering, generic praise that creates false confidence, **InterviewX** delivers **rigorous, evidence-based technical evaluations**, exposes dangerous misconceptions, and generates personalized day-wise study roadmaps to guarantee placement success.

---

## 🛠️ Technology Stack

- **Frontend & App Framework**: [Streamlit](https://streamlit.io/) with custom HTML5/CSS3 design system
- **Backend & Modular Architecture**: Python 3.13+
- **AI Engine**: Google Gemini API (`gemini-2.5-flash`) with dynamic question generation & answer evaluation (with built-in offline audit mode fallback)
- **Database**: SQLite3 (Multi-user persistent storage with foreign key cascades and user data isolation)
- **Data & Charts**: Plotly & Pandas (Clean Score Progression Trendline & Competency Performance Breakdown Pie Chart — strictly no radar charts)
- **Document & Resume Ingestion**: Pure-Python DOCX extractor (`zipfile` + XML parsing) & PDF text stream decoder (`zlib`)
- **Report Generation**: Pure-Python PDF 1.4 report writer (`PDFReportGenerator`)

---

## 📁 Project Structure

```
InterviewX/
├── .env.example                # Template for environment variables (GEMINI_API_KEY)
├── .gitignore                  # Git exclusions for secrets, databases, and artifacts
├── requirements.txt            # Project dependencies
├── README.md                   # Comprehensive documentation
├── config.py                   # Centralized configuration, roles, tracks & secure env loaders
├── app.py                      # Main Streamlit application entry point & page router
├── auth/
│   ├── __init__.py             # Auth package exports
│   ├── security.py             # PBKDF2 salted password hashing & input validators
│   └── session_manager.py      # Streamlit session state management & user isolation
├── database/
│   ├── __init__.py
│   ├── connection.py           # SQLite connection manager & schema migrations
│   └── models.py               # Database schemas, CRUD queries & analytics computation
├── services/
│   ├── __init__.py
│   ├── gemini_service.py       # Google Gemini API client with strict honest prompts & fallback bank
│   └── analytics_service.py    # Metric aggregations, deltas & readiness calculations
├── components/
│   ├── __init__.py
│   ├── navbar.py               # Modern navigation sidebar, profile badge & key settings
│   ├── auth_forms.py           # Sign-in and registration forms with validation
│   ├── cards.py                # Metric boxes, honest feedback comparison widgets & badges
│   └── charts.py               # Interactive Plotly charts (score trendline & competency pie chart)
├── pages_modules/
│   ├── __init__.py
│   ├── landing.py              # High-converting landing page for Indian graduates
│   ├── dashboard.py            # Analytics dashboard, KPIs, competency pie chart & recent sessions
│   ├── resume_analyzer.py      # Resume text extractor, skill breakdown, ATS scoring & targeted questions
│   ├── interview.py            # Multi-turn AI Mock Interview Engine with live scoring
│   ├── feedback.py             # Post-Interview Feedback Report with downloadable PDF
│   ├── weakness_tracker.py     # Recurring technical weakness tracker & revision lifecycle
│   ├── roadmap.py              # Personalised Preparation Roadmap with daily SQLite task checkboxes
│   ├── analytics.py            # Long-term progress analytics, score progression & distributions
│   ├── history.py              # Historical archive with session inspector and deletion
│   └── profile.py              # Candidate profile editor, resume privacy manager & account deletion
├── utils/
│   ├── __init__.py
│   ├── resume_parser.py        # Pure-Python DOCX/PDF/TXT parser & ResumeAnalyzer
│   └── pdf_generator.py        # Pure-Python PDF 1.4 report generator
├── tests/
│   ├── test_full_platform.py   # Comprehensive end-to-end integration test suite (8/8 passing)
│   ├── test_database_enhancements.py
│   ├── test_interview_engine.py
│   ├── test_pdf_generator.py
│   └── test_resume_parser.py
└── static/
    └── styles.css              # Custom styling (glassmorphism, typography, color-coded badges)
```

---

## 🚀 Complete Platform Features

1. **Authentication & Multi-User Isolation**:
   - Secure registration, login, and logout.
   - Salted PBKDF2-HMAC-SHA256 password hashing.
   - Strict per-user SQLite data isolation: candidate profile, resumes, interview sessions, questions, feedback reports, weakness tracking, and roadmaps are completely isolated per user.

2. **Candidate Dashboard**:
   - Placement readiness index and KPI metric cards.
   - Score Progression Trendline vs. 75% placement target benchmark.
   - **Competency Performance Breakdown Pie Chart** (Technical Accuracy, Relevance, Completeness, Clarity & Communication using actual candidate evaluation scores — no radar charts).
   - Confirmed technical strengths and flagged recurring weaknesses.
   - Recent mock interview history with direct report navigation.

3. **Resume Analyzer & Targeted Prep**:
   - Drag-and-drop resume upload (PDF, DOCX, TXT) parsed via pure-Python extractors without external binary dependencies.
   - Identifies candidate skills, projects, work experience, and educational background.
   - Highlights missing or weak skills (e.g., CI/CD, testing, system design) and ATS optimization tips.
   - Generates tailored interview questions based on the candidate's exact tech stack and projects.
   - Single-click action to start a resume-tailored mock interview.

4. **Multi-Turn AI Mock Interview Engine**:
   - 12 comprehensive job roles (SDE-1, Backend, Frontend, Full Stack, Data Engineer, Machine Learning, Data Analyst, Cloud/DevOps, QA/Automation, Mobile, Cyber Security, Product Management).
   - 6 interview categories (Technical, System Design, Coding & Problem Solving, HR & Behavioral, Core CS Fundamentals, Resume-Deep Dive).
   - 3 difficulty tiers (Fresher / Campus, Intermediate 1-3 Yrs, Advanced Tier-1).
   - Asks one question at a time with dynamic, adaptive follow-ups based on the candidate's previous response.
   - Evaluates answers across 4 pillars out of 10: Technical Accuracy, Relevance, Completeness, and Clarity & Communication.
   - Robust offline audit fallback engine when API key is not configured.

5. **Post-Interview Feedback Report & PDF Export**:
   - Executive summary and campus placement readiness indicator.
   - Competency performance bar comparison against target benchmarks.
   - Detailed question-by-question breakdown showing candidate's answer, honest critique, technical misconceptions, missing points, and production-grade sample answers with explanations.
   - **Downloadable PDF Report**: Generated on-the-fly using a pure-Python PDF 1.4 emitter.

6. **Personalized Weakness Tracker**:
   - Automatically tracks technical concepts flagged during mock interviews.
   - Displays frequency of errors and diagnostic notes.
   - Interactive revision lifecycle status (`Needs Work` → `In Progress` → `Mastered`).
   - Manual weakness logging and deletion controls.

7. **Interactive Preparation Roadmap**:
   - 7-day, 14-day, and 30-day customized curriculums tailored to the candidate's target role and diagnosed weak areas.
   - Day-wise structured tasks with interactive completion checkboxes stored persistently in SQLite.
   - Live completion progress bar and roadmap archive.

8. **Progress Analytics**:
   - Quantitative evaluation trajectories and score progression over time.
   - Competency distribution and interview category distribution.
   - Placement readiness tracking.

9. **User Profile & Privacy Management**:
   - Edit personal, academic, and career alignment details.
   - Resume privacy manager with one-click permanent resume deletion.
   - Account deletion danger zone: permanently erases all candidate records, sessions, and roadmaps with cascading SQLite cleanup.

---

## ⚙️ Quick Start Guide

### 1. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add your free Google Gemini API Key:
```env
GEMINI_API_KEY=AIzaSyYourActualKeyHere
```
*(Note: If no API key is provided, the platform automatically runs in its intelligent offline audit mode with curated technical question banks and heuristic evaluation).*

### 2. Run the Application
Launch the application with Streamlit:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 3. Demo Credentials
To test immediately with pre-populated interview history, score trendlines, and roadmap data:
- **Username**: `arjun`
- **Password**: `Demo@123`
- Or register a new account from the sidebar navigation.

---

## 🧪 Running the Automated Test Suite

Run the full end-to-end integration test suite:
```bash
python -m unittest tests/test_full_platform.py -v
```
All 8 integration tests test the complete candidate lifecycle:
- Authentication & profile updates
- Resume parsing & skill extraction
- Mock interview engine & criteria scoring
- User data isolation
- Weakness tracker revision lifecycle
- Interactive preparation roadmap & task persistence
- Pure-Python PDF feedback report generation
- Cascading account deletion
