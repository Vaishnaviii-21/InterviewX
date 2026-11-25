"""
Configuration module for InterviewX.
Handles environment variables, constants, job roles, and platform settings.
"""

import os
import sys
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATABASE_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "interviewx.db"))

def load_environment():
    """
    Safely load environment variables from .env file without external dependencies
    if python-dotenv is not installed.
    """
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip('"').strip("'")
                        # Set if not in os.environ or if current value is empty/placeholder
                        curr = os.environ.get(key, "").strip()
                        if not curr or curr == "your_gemini_api_key_here":
                            os.environ[key] = val
        except Exception as e:
            print(f"[Warning] Error reading .env file: {e}")

# Load environment on import
load_environment()

# Brand Identity
APP_NAME = "InterviewX"
TAGLINE = "Practice. Get Honest Feedback. Improve. Get Hired."
TARGET_AUDIENCE = "Indian college students, fresh graduates and job seekers"
VERSION = "1.0.0-stage1"

# Readiness & System Benchmarks
READINESS_TARGET_BENCHMARK = 75.0
READINESS_POLISH_BENCHMARK = 60.0
READINESS_READY_BENCHMARK = 80.0
MAX_RESUME_FILE_SIZE = 5 * 1024 * 1024

# Accessible Brand Colors
COLOR_SUCCESS = "#10B981"
COLOR_WARNING = "#F59E0B"
COLOR_DANGER = "#EF4444"
COLOR_PRIMARY = "#4F46E5"

# Target Job Roles relevant for Indian Campus Placements & Off-campus Drives
JOB_ROLES = [
    {
        "id": "software_developer",
        "title": "Software Developer",
        "category": "Software Engineering",
        "description": "Core CS, Data Structures, Algorithms, OOP, and problem solving.",
        "icon": "💻",
        "core_topics": ["Data Structures", "Algorithms", "OOP Concepts", "DBMS & SQL", "Operating Systems", "Computer Networks"]
    },
    {
        "id": "python_developer",
        "title": "Python Developer",
        "category": "Software Engineering",
        "description": "Python internals, OOP, multithreading/multiprocessing, Django/FastAPI, and API design.",
        "icon": "🐍",
        "core_topics": ["Python Internals (GIL, Memory)", "FastAPI / Django", "Decorators & Generators", "SQLAlchemy & Databases", "Asyncio & Concurrency"]
    },
    {
        "id": "java_developer",
        "title": "Java Developer",
        "category": "Software Engineering",
        "description": "Core Java, JVM internals, Collections, Multithreading, and Spring Boot framework.",
        "icon": "☕",
        "core_topics": ["Core Java & OOPS", "JVM Architecture & GC", "Collections Framework", "Spring Boot & REST", "Microservices & Hibernate"]
    },
    {
        "id": "frontend_dev",
        "title": "Frontend Developer",
        "category": "Software Engineering",
        "description": "JavaScript ES6+, React.js ecosystem, state management, CSS/Tailwind, and web performance.",
        "icon": "🎨",
        "core_topics": ["JavaScript ES6+", "React.js Hooks & DOM", "CSS3 / Responsive Design", "State Management (Redux/Zustand)", "Web Performance & Core Web Vitals"]
    },
    {
        "id": "backend_dev",
        "title": "Backend Developer",
        "category": "Software Engineering",
        "description": "REST APIs, Database Design, Caching, Concurrency, and Microservices architecture.",
        "icon": "⚙️",
        "core_topics": ["REST & GraphQL APIs", "Database Indexing & Transactions", "Caching (Redis)", "Microservices Architecture", "Authentication & Security"]
    },
    {
        "id": "fullstack_dev",
        "title": "Full Stack Developer",
        "category": "Software Engineering",
        "description": "End-to-end web applications combining React/Next.js with Node/Python/Java backends and databases.",
        "icon": "🌐",
        "core_topics": ["Frontend Architecture", "REST API Integration", "Relational & NoSQL Databases", "Authentication Flows", "Cloud Deployment"]
    },
    {
        "id": "data_analyst",
        "title": "Data Analyst",
        "category": "Data & Analytics",
        "description": "SQL querying, Excel modeling, PowerBI/Tableau dashboards, and business problem solving.",
        "icon": "📊",
        "core_topics": ["Advanced SQL (Window Functions, CTEs)", "Python (Pandas, NumPy)", "Data Visualization", "Business Metrics & KPI Analysis", "Statistical Testing"]
    },
    {
        "id": "data_scientist",
        "title": "Data Scientist",
        "category": "AI & Data Science",
        "description": "Statistical modeling, supervised/unsupervised machine learning, feature engineering, and analytics.",
        "icon": "🔬",
        "core_topics": ["Probability & Statistics", "Supervised Learning", "Unsupervised Learning", "Feature Engineering", "Model Evaluation Metrics"]
    },
    {
        "id": "ml_engineer",
        "title": "Machine Learning Engineer",
        "category": "AI & Data Science",
        "description": "ML algorithms, PyTorch/TensorFlow, model deployment, pipelines, and inference optimization.",
        "icon": "🤖",
        "core_topics": ["Deep Learning & Neural Networks", "PyTorch / TensorFlow", "MLOps & Model Deployment", "Feature Stores & Pipelines", "Model Optimization"]
    },
    {
        "id": "ai_engineer",
        "title": "AI Engineer",
        "category": "AI & Data Science",
        "description": "Modern AI application engineering, APIs, vector databases, search, and agentic workflows.",
        "icon": "🧠",
        "core_topics": ["Embeddings & Vector Databases", "Semantic Search & RAG", "Model Fine-Tuning", "API Integration", "Agent Architectures"]
    },
    {
        "id": "genai_engineer",
        "title": "Generative AI Engineer",
        "category": "AI & Data Science",
        "description": "Large Language Models, prompt engineering, RAG pipelines, fine-tuning, and LLM orchestration.",
        "icon": "✨",
        "core_topics": ["LLM Architectures & Transformers", "RAG (Retrieval-Augmented Generation)", "Prompt Engineering & Evaluation", "LangChain / LlamaIndex", "Vector DBs (Chroma/Pinecone)"]
    },
    {
        "id": "devops_engineer",
        "title": "DevOps Engineer",
        "category": "Cloud & Infrastructure",
        "description": "CI/CD pipelines, Docker containerization, Kubernetes, Linux administration, and AWS/Cloud.",
        "icon": "☁️",
        "core_topics": ["Linux Administration", "Docker & Containers", "Kubernetes Orchestration", "CI/CD (GitHub Actions/Jenkins)", "AWS / Cloud Infrastructure"]
    }
]

# Interview Categories
INTERVIEW_CATEGORIES = [
    {"id": "technical", "name": "Technical Interview", "icon": "💻", "desc": "DSA, system architecture, database design, and framework mechanics."},
    {"id": "hr", "name": "HR Interview", "icon": "🤝", "desc": "Career aspirations, cultural fit, strengths, weaknesses, and salary expectations."},
    {"id": "behavioral", "name": "Behavioral Interview", "icon": "🎯", "desc": "Scenario questions using the structured STAR methodology."},
    {"id": "coding", "name": "Coding Interview", "icon": "⌨️", "desc": "Algorithmic logic, edge cases, time/space complexity, and code design."},
    {"id": "resume", "name": "Resume-Based Interview", "icon": "📄", "desc": "Deep dive into your claimed projects, tech stack, and internship experiences."},
    {"id": "mixed", "name": "Mixed Interview", "icon": "🔀", "desc": "Comprehensive simulation combining Technical and HR/Behavioral questions."}
]

# Interview Durations
INTERVIEW_DURATIONS = [
    {"minutes": 5, "label": "5 Minutes (Quick Warmup - 3 Questions)"},
    {"minutes": 10, "label": "10 Minutes (Standard Screen - 5 Questions)"},
    {"minutes": 15, "label": "15 Minutes (In-Depth Assessment - 8 Questions)"},
    {"minutes": 30, "label": "30 Minutes (Full Placement Simulation - 10 Questions)"}
]

# Difficulty Levels
DIFFICULTY_LEVELS = [
    {
        "id": "beginner",
        "name": "Beginner (Campus Placements / Freshers)",
        "badge": "Beginner",
        "description": "Foundational conceptual questions, basic coding scenarios, definitions, and core CS fundamentals.",
        "target": "TCS NQT, Infosys, Wipro, Cognizant, Capgemini & Service-based IT Drives."
    },
    {
        "id": "intermediate",
        "name": "Intermediate (1-2 Years / Product Startups)",
        "badge": "Intermediate",
        "description": "Practical application, code edge cases, optimization, schema design, and scenario questions.",
        "target": "Fintech firms, Series A/B Indian startups, Mid-tier Product companies."
    },
    {
        "id": "advanced",
        "name": "Advanced (Tier-1 Product / FAANG)",
        "badge": "Advanced",
        "description": "In-depth distributed systems, hard DSA optimization, concurrency pitfalls, and high-stakes architecture.",
        "target": "Google, Amazon, Microsoft, Uber, Flipkart, Swiggy, Cred, Zomato."
    }
]

# Target Company Categories
COMPANY_TRACKS = [
    {"id": "product", "name": "Product Companies & Tier-1 Startups", "icon": "🚀"},
    {"id": "services", "name": "IT Services & Mass Recruiters (TCS, Infosys, etc.)", "icon": "🏢"},
    {"id": "fintech", "name": "Fintech, Global In-house Centers (GICs) & Banks", "icon": "💳"}
]

# Target Company Tiers & Recruitment Tracks
COMPANY_TIERS = [
    {
        "id": "tier1_product",
        "name": "Product / Tier-1 Tech (FAANG/MAANG)",
        "badge": "Tier-1 Product",
        "icon": "🚀",
        "description": "High-scale engineering, distributed systems, deep DSA, and low-level system design.",
        "target_companies": "Google, Amazon, Microsoft, Uber, Atlassian, Apple"
    },
    {
        "id": "unicorns_startups",
        "name": "High-Growth Tech Startups",
        "badge": "Growth Startups",
        "icon": "🦄",
        "description": "Fast-paced feature delivery, modern full-stack tech stacks, microservices, and system architecture.",
        "target_companies": "Flipkart, Swiggy, Zomato, CRED, Razorpay, Zepto, Meesho"
    },
    {
        "id": "fintech_banking",
        "name": "FinTech & Banking",
        "badge": "Fintech & GCCs",
        "icon": "💳",
        "description": "High transaction throughput, ACID compliance, financial security, and distributed data pipelines.",
        "target_companies": "Goldman Sachs, Morgan Stanley, JP Morgan Chase, BNY Mellon, American Express"
    },
    {
        "id": "it_services",
        "name": "IT Services / Mass Recruiters",
        "badge": "IT Services",
        "icon": "🏢",
        "description": "Core CS fundamentals, quantitative aptitude, OOP, SQL, and business communication.",
        "target_companies": "TCS (Digital/Ninja), Infosys (SP/DSE/SE), Wipro, Cognizant, Capgemini, Accenture"
    },
    {
        "id": "enterprise_saas",
        "name": "Enterprise Software & SaaS",
        "badge": "Enterprise SaaS",
        "icon": "💼",
        "description": "Multi-tenant architectures, cloud integrations, API ecosystems, and scalable databases.",
        "target_companies": "Salesforce, Oracle, SAP, Adobe, Cisco, VMware"
    }
]

# Evaluation Metrics for the Honest Feedback Engine
EVALUATION_METRICS = [
    {
        "name": "Accuracy",
        "weight": 0.35,
        "description": "Are the technical concepts, syntax, definitions, and facts correct?"
    },
    {
        "name": "Relevance",
        "weight": 0.25,
        "description": "Did the answer directly address the interviewer's question without beating around the bush?"
    },
    {
        "name": "Completeness",
        "weight": 0.20,
        "description": "Were all key components, edge cases, trade-offs, and details addressed?"
    },
    {
        "name": "Clarity & Structure",
        "weight": 0.20,
        "description": "Was the answer communicated in a structured, concise, and professional manner?"
    }
]

def mask_api_key(key: str) -> str:
    """Safely masks an API key, showing only the first 4 and last 4 characters."""
    if not key or len(key) <= 8:
        return "••••••••"
    return f"{key[:4]}...{key[-4:]}"

def get_gemini_api_key() -> str:
    """
    Retrieve Gemini API key safely from:
    1. Streamlit session_state (user's active browser session)
    2. OS environment variables (os.environ)
    3. Project .env file
    4. Streamlit secrets
    Never returns hardcoded placeholder keys.
    """
    # 1. Check Streamlit session_state first (supports runtime sidebar session input)
    try:
        import streamlit as st
        if hasattr(st, "session_state") and st.session_state.get("gemini_api_key"):
            s_val = str(st.session_state["gemini_api_key"]).strip()
            if s_val and s_val != "your_gemini_api_key_here":
                return s_val
    except Exception:
        pass

    # 2. Check OS environment variable
    key = os.environ.get("GEMINI_API_KEY", "")
    if key and key.strip() and key.strip() != "your_gemini_api_key_here":
        return key.strip()

    # 3. Direct check of .env file (if not yet loaded into os.environ)
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() == "GEMINI_API_KEY":
                            val = v.strip().strip('"').strip("'")
                            if val and val != "your_gemini_api_key_here":
                                os.environ["GEMINI_API_KEY"] = val
                                return val
        except Exception:
            pass

    # 4. Check Streamlit secrets if running inside streamlit
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            s_key = st.secrets["GEMINI_API_KEY"]
            if s_key and s_key.strip() and s_key.strip() != "your_gemini_api_key_here":
                return s_key.strip()
    except Exception:
        pass

    return ""

def set_gemini_api_key(key: str, persist_to_env: bool = False) -> bool:
    """
    Sets the active Gemini API key in session state and os.environ.
    Optionally persists to local .env file if requested by user.
    """
    clean_key = (key or "").strip()
    if not clean_key or clean_key == "your_gemini_api_key_here":
        return False

    # Set in os.environ for backend calls
    os.environ["GEMINI_API_KEY"] = clean_key

    # Set in session_state for Streamlit persistence across reruns
    try:
        import streamlit as st
        st.session_state["gemini_api_key"] = clean_key
    except Exception:
        pass

    # Optionally persist to .env file
    if persist_to_env:
        try:
            env_file = BASE_DIR / ".env"
            lines = []
            replaced = False
            if env_file.exists():
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("GEMINI_API_KEY="):
                            lines.append(f"GEMINI_API_KEY={clean_key}\n")
                            replaced = True
                        else:
                            lines.append(line)
            if not replaced:
                lines.append(f"GEMINI_API_KEY={clean_key}\n")
            with open(env_file, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception:
            pass

    return True

def clear_gemini_api_key():
    """Clears API key from session state, environment, and optionally .env."""
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]
    try:
        import streamlit as st
        if "gemini_api_key" in st.session_state:
            del st.session_state["gemini_api_key"]
    except Exception:
        pass

def is_api_key_configured() -> bool:
    """Check if a valid Gemini API key is configured."""
    key = get_gemini_api_key()
    return bool(key and len(key) >= 15 and key != "your_gemini_api_key_here")
