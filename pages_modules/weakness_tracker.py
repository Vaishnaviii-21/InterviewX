"""
Personalized Weakness Tracker module for InterviewX.
Aggregates recurring weaknesses and technical gaps detected across mock interview sessions:
- Analyzes frequency of detected misconceptions
- Manages revision status (Needs Work, In Progress, Mastered)
- Provides tailored practice questions for each recurring gap
- Connects directly to study roadmap generator
"""

import streamlit as st
from auth import get_current_user, is_authenticated
from database import (
    get_all_user_topics,
    update_topic_revision_status,
    delete_user_topic,
    record_topic_status
)

def render_weakness_tracker_page():
    """Renders the comprehensive Weakness Tracker dashboard."""
    st.markdown("## ⚠️ Personalized Weakness & Competency Tracker")
    st.markdown(
        "InterviewX automatically indexes technical gaps, syntax errors, and incomplete concepts "
        "detected during your interviews. Track your revision progress and prioritize your preparation."
    )

    logged_in = is_authenticated()
    curr_user = get_current_user()
    user_id = curr_user["id"] if (logged_in and curr_user) else 1

    all_topics = get_all_user_topics(user_id)
    weaknesses = [t for t in all_topics if t.get("status") == "weakness"]
    strengths = [t for t in all_topics if t.get("status") == "strength"]

    # Top KPI Metrics Row
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    with col_kpi1:
        st.metric("Total Identified Gaps", len(weaknesses))
    with col_kpi2:
        in_progress = len([w for w in weaknesses if w.get("revision_status") == "In Progress"])
        st.metric("Active Revision", in_progress)
    with col_kpi3:
        mastered = len([w for w in weaknesses if w.get("revision_status") == "Mastered"])
        st.metric("Mastered Concepts", mastered)
    with col_kpi4:
        st.metric("Verified Strengths", len(strengths))

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # Action Banner: Launch Roadmap
    if weaknesses:
        col_banner1, col_banner2 = st.columns([2.5, 1], vertical_alignment="center")
        with col_banner1:
            st.info("💡 **Ready to eliminate these recurring weaknesses?** Generate a customized day-by-day study roadmap based on your active gaps.", icon="🗺️")
        with col_banner2:
            if st.button("🗺️ Generate Study Plan", type="primary", width="stretch"):
                st.session_state["active_page"] = "roadmap"
                st.rerun()

    st.markdown("### 🔍 Recurring Technical Weaknesses")

    if not weaknesses:
        st.info(
            "🎉 **No active recurring weaknesses identified!** Complete more mock interviews to audit "
            "your technical depth and identify targeted concepts to refine.",
            icon="✨"
        )
    else:
        # Filter tabs
        tab_all, tab_high, tab_mastered = st.tabs(["All Active Gaps", "High Frequency (2x+)", "Mastered"])

        with tab_all:
            _render_topic_list(weaknesses, user_id)

        with tab_high:
            high_freq = [w for w in weaknesses if w.get("frequency", 1) >= 2]
            if high_freq:
                _render_topic_list(high_freq, user_id)
            else:
                st.caption("No topics have been flagged multiple times yet.")

        with tab_mastered:
            mastered_list = [w for w in weaknesses if w.get("revision_status") == "Mastered"]
            if mastered_list:
                _render_topic_list(mastered_list, user_id)
            else:
                st.caption("No topics marked as mastered yet. Mark items as mastered once you revise them!")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Verified Strengths Section
    st.markdown("### 🏆 Confirmed Technical Strengths")
    if not strengths:
        st.caption("Complete more mock interviews to verify your core technical strengths.")
    else:
        col_s1, col_s2 = st.columns(2)
        for idx, s in enumerate(strengths):
            col_target = col_s1 if idx % 2 == 0 else col_s2
            with col_target:
                st.markdown(f"""
                <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 12px; padding: 1rem; margin-bottom: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 700; color: #166534; font-size: 0.95rem;">✅ {s['topic_name']}</span>
                        <span style="background: #DCFCE7; color: #15803D; font-size: 0.75rem; font-weight: 700; padding: 2px 8px; border-radius: 6px;">
                            Verified {s['frequency']}x
                        </span>
                    </div>
                    <div style="font-size: 0.78rem; color: #166534; margin-top: 4px;">Category: {s.get('category', 'Technical')}</div>
                    <div style="font-size: 0.82rem; color: #14532D; margin-top: 6px; line-height: 1.4;">
                        <i>{s.get('notes', '')}</i>
                    </div>
                </div>
                """, unsafe_allow_html=True)

def _render_topic_list(topic_list, user_id: int):
    """Renders individual weakness items with status controls and practice questions."""
    for t in topic_list:
        t_id = t["id"]
        t_name = t["topic_name"]
        t_cat = t.get("category", "Technical")
        freq = t.get("frequency", 1)
        notes = t.get("notes", "")
        status = t.get("revision_status", "Needs Work")

        status_colors = {
            "Needs Work": ("#FEF2F2", "#991B1B", "#FECACA"),
            "In Progress": ("#FFFBEB", "#92400E", "#FDE68A"),
            "Mastered": ("#F0FDF4", "#166534", "#BBF7D0")
        }
        bg, fg, border = status_colors.get(status, status_colors["Needs Work"])

        with st.container():
            st.markdown(f"""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 1.15rem; margin-bottom: 0.85rem; box-shadow: 0 2px 8px rgba(15, 23, 42, 0.02);">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                    <div>
                        <span style="font-weight: 700; color: #0F172A; font-size: 1rem;">⚠️ {t_name}</span>
                        <div style="font-size: 0.78rem; color: #64748B; margin-top: 2px;">
                            Category: {t_cat} • Flagged {freq} time(s) • Last Evaluated: {str(t.get('last_evaluated', ''))[:10]}
                        </div>
                    </div>
                    <div style="background: {bg}; color: {fg}; border: 1px solid {border}; font-size: 0.75rem; font-weight: 700; padding: 3px 10px; border-radius: 8px;">
                        Status: {status}
                    </div>
                </div>
                <div style="font-size: 0.85rem; color: #334155; margin-top: 8px; line-height: 1.45; border-top: 1px solid #F1F5F9; padding-top: 8px;">
                    <b>Detected Mistake / Critique:</b> {notes or 'Incomplete technical depth detected during answer evaluation.'}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Interactive Controls Row
            c_stat, c_del = st.columns([3, 1], vertical_alignment="center")
            with c_stat:
                new_status = st.selectbox(
                    f"Update revision status for '{t_name[:25]}...':",
                    ["Needs Work", "In Progress", "Mastered"],
                    index=["Needs Work", "In Progress", "Mastered"].index(status) if status in ["Needs Work", "In Progress", "Mastered"] else 0,
                    key=f"status_sel_{t_id}",
                    label_visibility="collapsed"
                )
                if new_status != status:
                    update_topic_revision_status(t_id, user_id, new_status)
                    st.success(f"Updated status of '{t_name}' to '{new_status}'!")
                    st.rerun()

            with c_del:
                if st.button("🗑️ Remove", key=f"del_topic_{t_id}", help="Remove topic from tracking"):
                    delete_user_topic(t_id, user_id)
                    st.success("Topic removed.")
                    st.rerun()
