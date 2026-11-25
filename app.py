"""
Main entry point for InterviewX.
AI-Powered Interview Preparation Platform for Indian college students and fresh graduates.
# Practice. Get Honest Feedback. Improve. Get Hired.
"""

import sys
import os
from pathlib import Path
import streamlit as st

# Configure Streamlit page settings before any other Streamlit calls
st.set_page_config(
    page_title="InterviewX | Practice. Get Honest Feedback. Improve. Get Hired.",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import APP_NAME, TAGLINE, STATIC_DIR
from database.connection import init_db
from database.models import seed_demo_data_if_empty
from auth import init_session_state, is_authenticated
from components.navbar import render_sidebar
from components.auth_forms import render_auth_page
from pages_modules import (
    render_landing_page,
    render_dashboard,
    render_resume_analyzer_page,
    render_interview_page,
    render_feedback_page,
    render_weakness_tracker_page,
    render_roadmap_page,
    render_analytics_page,
    render_history_page,
    render_profile_page,
)

def load_custom_css():
    """Injects custom CSS from static/styles.css into the Streamlit app."""
    css_file = STATIC_DIR / "styles.css"
    if css_file.exists():
        try:
            with open(css_file, "r", encoding="utf-8") as f:
                css_content = f.read()
                st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Could not load custom styles: {e}")

def initialize_application():
    """Initializes SQLite database, runs migrations, and seeds demo records if fresh."""
    try:
        init_db()
        seed_demo_data_if_empty()
    except Exception as e:
        st.error(f"Database initialization error: {e}")

def main():
    # 1. Initialize session state
    init_session_state()

    # 2. Apply custom CSS
    load_custom_css()

    # 3. Initialize database
    initialize_application()

    # 4. Render Navigation Sidebar
    selected_page = render_sidebar()

    # 4b. Guard protected dashboard and private candidate pages
    PROTECTED_PAGES = {"dashboard", "profile", "history", "analytics", "weakness_tracker", "roadmap"}
    if not is_authenticated() and selected_page in PROTECTED_PAGES:
        selected_page = "auth"
        st.session_state["active_page"] = "auth"

    # Accessible Skip to Content Link & Main Anchor (WCAG 2.4.1 Bypass Blocks)
    st.markdown('<a href="#main-content" class="skip-to-content">Skip to main content</a><div id="main-content" tabindex="-1"></div>', unsafe_allow_html=True)

    # 5. Route to target page module
    try:
        if selected_page == "landing":
            render_landing_page()
        elif selected_page == "auth":
            render_auth_page()
        elif selected_page == "dashboard":
            render_dashboard()
        elif selected_page == "resume_analyzer":
            render_resume_analyzer_page()
        elif selected_page == "interview":
            render_interview_page()
        elif selected_page == "feedback":
            render_feedback_page()
        elif selected_page == "weakness_tracker":
            render_weakness_tracker_page()
        elif selected_page == "roadmap":
            render_roadmap_page()
        elif selected_page == "analytics":
            render_analytics_page()
        elif selected_page == "history":
            render_history_page()
        elif selected_page == "profile":
            render_profile_page()
        else:
            render_landing_page()
    except Exception as e:
        st.error(f"An unexpected error occurred while rendering the page: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()
