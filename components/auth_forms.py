"""
Authentication UI components for InterviewX.
Provides responsive, professional tabbed Login and Signup forms with input validation
and a 1-click demo login option for immediate testing.
"""

import textwrap
from typing import Optional, Callable
import streamlit as st
from config import JOB_ROLES, COMPANY_TRACKS
from database.models import authenticate_user, create_user
from auth.session_manager import login_user, is_authenticated

def render_auth_page():
    """
    Renders the dedicated, clean Authentication page with Sign In and Registration tabs.
    """
    if is_authenticated():
        st.success("You are already logged in!")
        if st.button("Go to Candidate Dashboard", type="primary", width="stretch"):
            st.session_state["active_page"] = "dashboard"
            st.rerun()
        return

    # Container Card Header
    auth_header_html = textwrap.dedent("""\
<div class="auth-header-card">
<div style="display: inline-flex; align-items: center; gap: 8px; background: #EEF2FF; color: #4F46E5; padding: 4px 12px; border-radius: 9999px; font-weight: 700; font-size: 0.8rem; margin-bottom: 0.75rem;">
<span>🔒</span> Secure Candidate Portal
</div>
<h2 style="font-size: 1.85rem; font-weight: 800; color: #0F172A; margin: 0 0 0.5rem 0; letter-spacing: -0.02em;">
Welcome to <span style="color: #4F46E5;">InterviewX</span>
</h2>
<p style="font-size: 0.925rem; color: #64748B; margin: 0; line-height: 1.5;">
Sign in to access your mock interview transcripts, resume analysis, and placement roadmaps.
</p>
</div>""").strip()
    st.markdown(auth_header_html, unsafe_allow_html=True)

    tab_signin, tab_signup = st.tabs(["🔑 Sign In", "📝 Create Account"])

    # ==================== TAB 1: SIGN IN ====================
    with tab_signin:
        st.markdown('<div class="dashboard-spacer-sm"></div>', unsafe_allow_html=True)
        
        with st.form("signin_form", clear_on_submit=False):
            login_id = st.text_input(
                "Username or Email",
                placeholder="e.g., arjun or student@college.edu",
                help="Enter your registered username or email address."
            )
            login_pwd = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password"
            )
            
            submit_login = st.form_submit_button(
                "Sign In to InterviewX",
                type="primary",
                width="stretch"
            )

            if submit_login:
                if not login_id or not login_pwd:
                    st.error("Please enter both your username/email and password.")
                else:
                    user, err = authenticate_user(login_id, login_pwd)
                    if user:
                        login_user(user)
                        st.toast(f"Welcome back, {user.get('name', 'Candidate')}! 🎉")
                        st.session_state["active_page"] = "dashboard"
                        st.rerun()
                    else:
                        st.error(err or "Authentication failed. Please verify credentials.")

        # Quick 1-Click Demo Login Box
        st.markdown("---")
        demo_box_html = textwrap.dedent("""\
<div class="demo-login-box">
<div style="font-weight: 700; font-size: 0.88rem; color: #3730A3; display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
<span>⚡</span> Quick Testing: 1-Click Demo Student
</div>
<div style="font-size: 0.8rem; color: #4338CA; line-height: 1.4;">
Instantly log in as <b>Arjun Verma</b> (NIT '26, SDE-1 Candidate) with pre-loaded mock sessions, past scores, and weakness trends.
</div>
</div>""").strip()
        st.markdown(demo_box_html, unsafe_allow_html=True)
        st.markdown('<div style="height: 6px;"></div>', unsafe_allow_html=True)

        if st.button("🚀 Sign In as Demo Student (Arjun Verma)", width="stretch"):
            user, err = authenticate_user("arjun", "Demo@123")
            if user:
                login_user(user)
                st.toast("Signed in as Demo Candidate (Arjun Verma)!")
                st.session_state["active_page"] = "dashboard"
                st.rerun()
            else:
                st.error("Demo account not found. Please reload demo data from sidebar.")

    # ==================== TAB 2: CREATE ACCOUNT ====================
    with tab_signup:
        st.markdown('<div class="dashboard-spacer-sm"></div>', unsafe_allow_html=True)

        with st.form("signup_form", clear_on_submit=False):
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                new_name = st.text_input("Full Name *", placeholder="e.g., Rohit Sharma")
                new_username = st.text_input("Username *", placeholder="e.g., rohit_26", help="Letters, numbers, and underscores (3-30 chars).")
            with col_u2:
                new_email = st.text_input("Email Address *", placeholder="e.g., rohit@iitb.ac.in")
                new_pwd = st.text_input("Password *", type="password", placeholder="Min 6 characters")

            new_pwd_confirm = st.text_input("Confirm Password *", type="password", placeholder="Re-enter password")

            st.markdown("##### 🎓 Academic & Placement Target")
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                new_college = st.text_input("College / Institute", value="Engineering Institute")
                new_degree = st.text_input("Degree", value="B.Tech in Computer Science")
            with col_a2:
                new_grad_year = st.selectbox("Graduation Year", [2024, 2025, 2026, 2027, 2028], index=2)
                role_options = [r["title"] for r in JOB_ROLES]
                new_role = st.selectbox("Target Job Role", role_options, index=0)

            track_options = [t["name"] for t in COMPANY_TRACKS]
            new_track = st.selectbox("Target Company Track", track_options, index=0)

            submit_signup = st.form_submit_button(
                "Create My Account & Start Preparation",
                type="primary",
                width="stretch"
            )

            if submit_signup:
                if new_pwd != new_pwd_confirm:
                    st.error("Passwords do not match. Please re-enter.")
                else:
                    new_user, err = create_user(
                        username=new_username,
                        email=new_email,
                        password=new_pwd,
                        name=new_name,
                        college=new_college,
                        degree=new_degree,
                        graduation_year=new_grad_year,
                        target_role=new_role,
                        target_company_track=new_track
                    )
                    if new_user:
                        login_user(new_user)
                        st.toast("🎉 Account created successfully! Welcome to InterviewX.")
                        st.session_state["active_page"] = "dashboard"
                        st.rerun()
                    else:
                        st.error(err or "Registration failed. Please check inputs.")
