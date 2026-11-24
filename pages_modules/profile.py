"""
Candidate Profile and Account Management module for InterviewX.
Allows candidates to:
- Review and update their personal/academic profile and target career track
- Inspect and securely purge their uploaded resume for data privacy
- Permanently delete their account and associated interview history
"""

import streamlit as st
from config import JOB_ROLES, COMPANY_TIERS
from auth import get_current_user, is_authenticated, login_user, logout_user
from database import (
    get_user_by_id,
    update_user_profile,
    get_candidate_resume,
    delete_candidate_resume,
    delete_user_account
)

def render_profile_page():
    """Renders the Candidate Profile & Account Settings view."""
    st.markdown("## 👤 Candidate Profile & Settings")
    st.markdown(
        "Manage your personal details, career target, privacy settings, and account data. "
        "Your interview evaluations and roadmaps adapt directly to your target role."
    )

    if not is_authenticated():
        st.info("Please sign in or register to manage your personal profile and settings.", icon="ℹ️")
        if st.button("🔑 Sign In / Register", type="primary"):
            st.session_state["active_page"] = "auth"
            st.rerun()
        return

    curr_user = get_current_user()
    user_id = curr_user["id"]
    
    # Reload fresh user info from DB
    fresh_user = get_user_by_id(user_id)
    if fresh_user:
        curr_user = fresh_user

    # Tabbed Interface: Profile Details | Resume & Privacy | Danger Zone
    tab_profile, tab_resume, tab_danger = st.tabs([
        "✏️ Profile Details",
        "📄 Resume & Privacy",
        "⚠️ Account & Danger Zone"
    ])

    with tab_profile:
        st.markdown("### Edit Your Career & Academic Profile")
        with st.form("edit_profile_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name", value=curr_user.get("name", "") or "")
                email = st.text_input("Email Address", value=curr_user.get("email", "") or "")
                college = st.text_input("College / University", value=curr_user.get("college", "") or "")
            
            with col2:
                # Degree selection
                degrees = ["B.Tech / B.E. (Computer Science / IT)", "B.Tech / B.E. (Other Branches)", "BCA / MCA", "B.Sc / M.Sc (CS/IT)", "Other"]
                curr_degree = curr_user.get("degree", degrees[0]) or degrees[0]
                deg_idx = degrees.index(curr_degree) if curr_degree in degrees else 0
                degree = st.selectbox("Degree / Program", options=degrees, index=deg_idx)
                
                grad_year = st.number_input(
                    "Graduation Year",
                    min_value=2020,
                    max_value=2032,
                    value=int(curr_user.get("graduation_year", 2026) or 2026),
                    step=1
                )

            st.markdown("---")
            st.markdown("#### Career Alignment")
            col3, col4 = st.columns(2)
            with col3:
                # Target Role
                role_titles = [r["title"] if isinstance(r, dict) else r for r in JOB_ROLES]
                curr_role = curr_user.get("target_role", role_titles[0]) or role_titles[0]
                role_idx = role_titles.index(curr_role) if curr_role in role_titles else 0
                target_role = st.selectbox("Target Job Role", options=role_titles, index=role_idx)

            with col4:
                # Target Track / Company Tier
                tier_names = [t["name"] if isinstance(t, dict) else t for t in COMPANY_TIERS]
                curr_track = curr_user.get("target_company_track", tier_names[0]) or tier_names[0]
                track_idx = tier_names.index(curr_track) if curr_track in tier_names else 0
                target_track = st.selectbox("Target Company Track", options=tier_names, index=track_idx)

            submitted = st.form_submit_button("💾 Save Profile Changes", type="primary", width="stretch")
            if submitted:
                if not name.strip():
                    st.error("Full Name cannot be empty.")
                elif not email.strip() or "@" not in email:
                    st.error("Please enter a valid email address.")
                else:
                    updates = {
                        "name": name.strip(),
                        "email": email.strip(),
                        "college": college.strip(),
                        "degree": degree,
                        "graduation_year": int(grad_year),
                        "target_role": target_role,
                        "target_company_track": target_track,
                    }
                    success = update_user_profile(user_id, updates)
                    if success:
                        # Refresh session state
                        refreshed = get_user_by_id(user_id)
                        if refreshed:
                            login_user(refreshed)
                        st.success("✅ Profile updated successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to update profile. Please try again.")

    with tab_resume:
        st.markdown("### Resume Privacy & Management")
        st.markdown(
            "Under InterviewX privacy standards, your resume text and extracted skills are stored "
            "locally in your SQLite database. You can inspect or permanently delete your stored resume at any time."
        )

        resume = get_candidate_resume(user_id)
        if resume:
            col_r1, col_r2 = st.columns([3, 2])
            with col_r1:
                st.markdown(f"**Stored File:** `{resume.get('file_name', 'resume.pdf')}`")
                st.markdown(f"**Last Uploaded:** {resume.get('uploaded_at', 'Recently')}")
                st.markdown(f"**ATS Compatibility Score:** `{resume.get('ats_score', 75)}/100`")
                st.markdown(f"**Extracted Skills:** {resume.get('skills', 'None recorded')}")
            
            with col_r2:
                st.warning("⚠️ **Permanently Delete Resume**")
                st.caption(
                    "Deleting your resume removes all extracted resume text and skills from your profile. "
                    "Your past interview scores and feedback reports will be preserved."
                )
                confirm_del_resume = st.checkbox("I confirm I want to permanently delete my stored resume", key="del_res_cb")
                if st.button("🗑️ Delete Stored Resume", type="secondary", disabled=not confirm_del_resume, width="stretch"):
                    deleted = delete_candidate_resume(user_id)
                    if deleted:
                        st.success("Resume permanently deleted.")
                        st.rerun()
                    else:
                        st.error("Could not delete resume.")
        else:
            st.info("No resume is currently stored for your account.", icon="📄")
            st.markdown(
                "Upload your resume in the **Resume Analyzer** to get personalized interview questions "
                "targeted directly to your projects and tech stack."
            )
            if st.button("🚀 Go to Resume Analyzer", type="primary"):
                st.session_state["active_page"] = "resume_analyzer"
                st.rerun()

    with tab_danger:
        st.markdown("### ⚠️ Danger Zone: Delete Account")
        st.markdown(
            "Permanently delete your account and all associated records. "
            "This action is **irreversible**."
        )
        
        st.error(
            "**What will be permanently erased:**\n"
            "- Your candidate profile and credentials\n"
            "- All mock interview sessions and recorded scores\n"
            "- All question-level evaluations, honest feedback, and transcripts\n"
            "- Your personal weakness tracker items\n"
            "- Your custom preparation roadmaps and milestone tasks\n"
            "- Your uploaded resume data"
        )

        confirm_text = st.text_input(
            "Type **DELETE** in capital letters to confirm account deletion:",
            placeholder="DELETE"
        )
        
        if st.button("🚨 Permanently Delete My Entire Account", type="primary", disabled=(confirm_text.strip() != "DELETE"), width="stretch"):
            deleted = delete_user_account(user_id)
            if deleted:
                logout_user()
                st.success("Your account and all associated data have been permanently deleted.")
                st.rerun()
            else:
                st.error("Failed to delete account. Please try again.")
