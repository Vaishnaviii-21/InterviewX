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
