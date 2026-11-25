"""
Session state manager for InterviewX user authentication.
Ensures session isolation and access guards across Streamlit pages.
"""

from typing import Optional, Dict, Any
import streamlit as st

def init_session_state():
    """Initializes authentication variables in Streamlit session_state."""
    if "is_authenticated" not in st.session_state:
        st.session_state["is_authenticated"] = False
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if "active_page" not in st.session_state:
        st.session_state["active_page"] = "landing"

def login_user(user_dict: Dict[str, Any]):
    """
    Sets the active user in session state and marks the session as authenticated.
    """
    # Safe copy without password hash
    safe_user = {k: v for k, v in user_dict.items() if k != "password_hash"}
    st.session_state["user"] = safe_user
    st.session_state["is_authenticated"] = True

def logout_user():
    """
    Clears the authenticated user session and resets state,
    redirecting the candidate to the Sign In / Login page.
    Leaves user account and all saved database records completely intact.
    """
    st.session_state["user"] = None
    st.session_state["is_authenticated"] = False
    st.session_state["active_page"] = "auth"

    # Purge any transient in-memory session/interview caches
    if "active_interview" in st.session_state:
        del st.session_state["active_interview"]
    if "view_session_id" in st.session_state:
        del st.session_state["view_session_id"]
    if "use_resume_mode" in st.session_state:
        st.session_state["use_resume_mode"] = False
    if "active_roadmap_id" in st.session_state:
        del st.session_state["active_roadmap_id"]

def get_current_user() -> Optional[Dict[str, Any]]:
    """Returns the currently logged-in candidate profile or None."""
    if st.session_state.get("is_authenticated") and st.session_state.get("user"):
        return st.session_state["user"]
    return None

def is_authenticated() -> bool:
    """Returns True if a valid user session is active."""
    return bool(st.session_state.get("is_authenticated") and st.session_state.get("user"))

def render_auth_guard(feature_name: str = "this protected page") -> bool:
    """
    Renders a standardized, accessible authentication guard when unauthenticated.
    Returns True if authenticated (allowing the caller to proceed),
    or False if unauthenticated after rendering the login prompt.
    """
    if is_authenticated():
        return True

    clean_feature = str(feature_name).strip()
    st.markdown('<h1 id="main-content" class="page-title-h1" tabindex="-1">🔒 Protected Candidate Portal</h1>', unsafe_allow_html=True)
    st.warning(f"🔒 **Protected Page:** You must be signed in. Please sign in or register to access {clean_feature}.", icon="🔒")
    st.markdown(
        f"This section contains private candidate records, AI evaluations, and personalized preparation tools. "
        "Please sign in or create an account to view your data."
    )
    col_login, col_home = st.columns(2)
    with col_login:
        safe_key = clean_feature.lower().replace(" ", "_").replace("&", "and")
        if st.button("🔑 Sign In / Register", key=f"guard_login_{safe_key}", type="primary", width="stretch"):
            st.session_state["active_page"] = "auth"
            st.rerun()
    with col_home:
        if st.button("🏠 Back to Home", key=f"guard_home_{safe_key}", width="stretch"):
            st.session_state["active_page"] = "landing"
            st.rerun()
    return False
