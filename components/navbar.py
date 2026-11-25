"""
Navigation and Sidebar component for InterviewX.
Handles authenticated multi-user state, routing, profile status, and Gemini API key configuration.
"""

import os
import html
import textwrap
import streamlit as st
from config import (
    APP_NAME,
    TAGLINE,
    is_api_key_configured,
    get_gemini_api_key,
    set_gemini_api_key,
    clear_gemini_api_key,
    mask_api_key
)
from database.models import get_or_create_default_user, reset_database, seed_demo_data_if_empty
from auth import is_authenticated, get_current_user, logout_user

def render_sidebar() -> str:
    """
    Renders the modern, clean sidebar with dynamic authentication status,
    navigation links, profile badge, and system settings.
    Returns the selected page key.
    """
    with st.sidebar:
        # Accessible Skip to Main Content Link (WCAG 2.4.1 Bypass Blocks)
        # Placed as the very first element in the sidebar so that it is the absolute
        # first focusable element in the browser DOM order across all pages.
        # Keyboard users pressing Tab will immediately focus this link before the
        # navigation radio, candidate card, or logout button.
        st.markdown(
            '<a href="#main-content" class="skip-to-content" aria-label="Skip to main content" '
            'onclick="var el=document.getElementById(\'main-content\'); if(el){ el.tabIndex=-1; el.focus(); el.scrollIntoView({behavior:\'smooth\', block:\'start\'}); }">'
            'Skip to main content</a>',
            unsafe_allow_html=True
        )

        # App Branding Header
        brand_html = textwrap.dedent(f"""\
<div style="padding: 0.25rem 0 0.85rem 0;">
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
<div style="background: linear-gradient(135deg, #4F46E5, #7C3AED); width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 800; font-size: 1.2rem; box-shadow: 0 4px 10px rgba(79, 70, 229, 0.3);">
X
</div>
<div>
<span style="font-size: 1.35rem; font-weight: 800; color: #0F172A; letter-spacing: -0.02em;">Interview</span>
<span style="font-size: 1.35rem; font-weight: 800; color: #4F46E5;">X</span>
</div>
</div>
<div style="font-size: 0.78rem; font-weight: 600; color: #64748B; line-height: 1.3;">
{TAGLINE}
</div>
</div>""").strip()
        st.markdown(brand_html, unsafe_allow_html=True)

        st.markdown("---")

        # Dynamic Navigation Options based on Auth State
        logged_in = is_authenticated()
        user = get_current_user()

        if logged_in:
            page_options = {
                "landing": "🏠 Home",
                "dashboard": "📊 Candidate Dashboard",
                "resume_analyzer": "📄 Resume Analyzer",
                "interview": "🎙️ AI Mock Interview",
                "feedback": "📋 Feedback Report",
                "weakness_tracker": "⚠️ Weakness Tracker",
                "roadmap": "🗺️ Preparation Roadmap",
                "analytics": "📈 Progress Analytics",
                "history": "📁 Interview History",
                "profile": "👤 Profile & Settings",
            }
        else:
            page_options = {
                "landing": "🏠 Home",
                "auth": "🔑 Sign In / Register",
                "interview": "🎙️ AI Mock Interview",
                "resume_analyzer": "📄 Resume Analyzer",
            }

        # Sync with session_state if set externally
        default_idx = 0
        current_page = st.session_state.get("active_page", "landing")
        keys = list(page_options.keys())
        if current_page in keys:
            default_idx = keys.index(current_page)
        elif not logged_in:
            default_idx = keys.index("auth") if "auth" in keys else 0

        selected_label = st.radio(
            "Navigation",
            options=list(page_options.values()),
            index=default_idx,
            label_visibility="collapsed"
        )
        selected_key = [k for k, v in page_options.items() if v == selected_label][0]
        st.session_state["active_page"] = selected_key

        st.markdown("---")

        # Candidate Profile Card in Sidebar
        if logged_in and user:
            u_name = user.get("name", "Candidate")
            u_role = user.get("target_role", "Software Development Engineer (SDE-1)")
            u_college = user.get("college", "College")
            u_grad = user.get("graduation_year", 2026)
            u_uname = user.get("username", "")

            clean_uname = html.escape(str(u_name))
            clean_urole = html.escape(str(u_role))
            clean_ucollege = html.escape(str(u_college))
            clean_uuname = html.escape(str(u_uname))

            sidebar_prof_html = textwrap.dedent(f"""\
<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 0.85rem; margin-bottom: 0.75rem;" role="region" aria-label="Authenticated Candidate Badge">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
<span style="font-size: 0.72rem; font-weight: 700; color: #059669; text-transform: uppercase; letter-spacing: 0.05em;">
<span aria-hidden="true">●</span> Logged In
</span>
<span style="font-size: 0.75rem; color: #334155; font-family: monospace;">@{clean_uuname}</span>
</div>
<div style="font-weight: 700; font-size: 0.95rem; color: #0F172A;">
{clean_uname}
</div>
<div style="font-size: 0.8rem; color: #3730A3; font-weight: 600;">
{clean_urole}
</div>
<div style="font-size: 0.75rem; color: #334155; margin-top: 2px;">
<span aria-hidden="true">🎓</span> {clean_ucollege} • Class of {u_grad}
</div>
</div>""").strip()
            st.markdown(sidebar_prof_html, unsafe_allow_html=True)

            if st.button("🚪 Logout", key="sidebar_logout_btn", width="stretch", help="Sign out of your account"):
                logout_user()
                st.toast("Logged out successfully.")
                st.rerun()

        else:
            # Guest Profile Box
            guest_html = textwrap.dedent("""\
<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 0.85rem; margin-bottom: 0.75rem;">
<div style="font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">
Guest Session
</div>
<div style="font-weight: 700; font-size: 0.92rem; color: #0F172A;">
Not Signed In
</div>
<div style="font-size: 0.78rem; color: #64748B; margin-top: 2px; line-height: 1.35;">
Sign in to save your personal mock transcripts, scores, and roadmaps.
</div>
</div>""").strip()
            st.markdown(guest_html, unsafe_allow_html=True)

            if st.button("🔑 Sign In / Register", type="primary", width="stretch"):
                st.session_state["active_page"] = "auth"
                st.rerun()

        # Gemini API Key Status & Secure Configuration
        api_ready = is_api_key_configured()
        active_key = get_gemini_api_key()

        with st.expander("🔑 Gemini API Settings", expanded=not api_ready):
            if api_ready:
                st.success("Live AI Mode Active (Gemini 2.5 Flash)", icon="✅")
                st.caption(f"Active Key: `{mask_api_key(active_key)}`")

                col_test, col_clear = st.columns(2)
                with col_test:
                    if st.button("Ping AI", width="stretch", help="Test live connection to Gemini 2.5 Flash"):
                        with st.spinner("Pinging Gemini..."):
                            from services.gemini_service import GeminiService
                            res = GeminiService(active_key).test_connection()
                            if res.get("success"):
                                st.toast("✅ Live Gemini 2.5 Flash connection verified!")
                            else:
                                st.error(res.get("message", "Connection failed"))
                with col_clear:
                    if st.button("Remove Key", width="stretch", help="Clears key and falls back to Offline Mode"):
                        clear_gemini_api_key()
                        st.toast("API key cleared. Offline mode active.")
                        st.rerun()
            else:
                st.warning("Offline Mode Active (Key Not Detected)", icon="⚠️")
                st.caption(
                    "Paste your Google Gemini API key below to activate Live AI generation. "
                    "Get a free key from Google AI Studio (https://aistudio.google.com)."
                )

                custom_key = st.text_input(
                    "Enter API Key:",
                    type="password",
                    placeholder="AIzaSy...",
                    key="sidebar_gemini_key_input",
                    help="Your key is never hardcoded, exposed, or transmitted to any third party."
                )

                persist_env = st.checkbox(
                    "Save to local .env file",
                    value=True,
                    help="Saves to .env so you don't need to re-enter it on restart."
                )

                if st.button("⚡ Save & Activate Live AI", type="primary", width="stretch"):
                    clean = (custom_key or "").strip()
                    if not clean:
                        st.error("Please enter a valid API key.")
                    elif len(clean) < 15:
                        st.error("Invalid key format: Gemini API keys are at least 30 characters long.")
                    else:
                        with st.spinner("Verifying connection to Google Gemini 2.5 Flash..."):
                            from services.gemini_service import GeminiService
                            test_svc = GeminiService(clean)
                            test_res = test_svc.test_connection()

                            if test_res.get("success"):
                                set_gemini_api_key(clean, persist_to_env=persist_env)
                                st.success("✅ Connected to Google Gemini 2.5 Flash! Live AI Mode is now active.")
                                st.rerun()
                            else:
                                err_msg = test_res.get("message", "Connection test failed.")
                                # Check if it's network/offline block or auth error
                                if "403" in err_msg or "Invalid" in err_msg or "Permission" in err_msg:
                                    st.error("❌ Key verification failed: Invalid Gemini API key or missing permissions.")
                                elif "Network error" in err_msg or "timed out" in err_msg or "getaddrinfo" in err_msg:
                                    # Still save key if it looks well-formed but outbound network is blocked
                                    set_gemini_api_key(clean, persist_to_env=persist_env)
                                    st.warning(f"Key saved, but outbound network ping did not reach Google servers ({err_msg}). Operating in offline fallback when network is unavailable.")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Connection error: {err_msg}")

        # Database Management Helper
        with st.expander("🛠️ Demo Data Controls"):
            st.caption("Manage SQLite persistent demo interview records.")
            col_seed, col_reset = st.columns(2)
            with col_seed:
                if st.button("Reload Data", width="stretch"):
                    seed_demo_data_if_empty()
                    st.toast("Sample data reloaded!")
                    st.rerun()
            with col_reset:
                if st.button("Clear DB", width="stretch"):
                    reset_database()
                    st.toast("Database reset to clean state.")
                    st.rerun()

        st.markdown(
            '<div style="text-align: center; font-size: 0.75rem; color: #475569; margin-top: 1.5rem;">'
            'InterviewX v1.0 • Built with Gemini 2.5 &amp; Streamlit'
            '</div>',
            unsafe_allow_html=True
        )

    return selected_key
