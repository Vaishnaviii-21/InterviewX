"""
Personalised Preparation Roadmap module for InterviewX.
Generates structured 7-day, 14-day, and 30-day study plans targeting
the candidate's exact interview weaknesses:
- Day-wise learning goals, recommended study, and coding exercises
- Interactive task completion checkboxes with real-time SQLite persistence
- Overall progress tracking bar and saved roadmap history
"""

import json
import streamlit as st
from auth import get_current_user, is_authenticated, render_auth_guard
from database import (
    get_user_by_id,
    get_all_user_topics,
    save_roadmap_with_tasks,
    get_user_roadmaps,
    get_roadmap_by_id,
    toggle_roadmap_task,
    delete_roadmap
)
from services.gemini_service import GeminiService

def render_roadmap_page():
    """Renders the Personalised Preparation Roadmap page."""
    if not render_auth_guard("Personalised Preparation Roadmap"):
        return

    st.markdown('<h1 class="page-title-h1"><span aria-hidden="true">🗺️</span> Personalised Preparation Roadmap</h1>', unsafe_allow_html=True)
    st.markdown(
        "Bridge the technical gaps diagnosed during your mock interviews. Generate a "
        "**structured, day-by-day preparation roadmap** with interactive checkboxes to track your progress."
    )

    curr_user = get_current_user()
    user_id = curr_user["id"]
    user_record = get_user_by_id(user_id) or {"target_role": "Software Development Engineer (SDE-1)"}

    # Fetch weak topics from database
    all_topics = get_all_user_topics(user_id)
    weaknesses = [t for t in all_topics if t.get("status") == "weakness" and t.get("revision_status") != "Mastered"]

    # 1. Generator Panel
    with st.container():
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);">
            <div style="font-weight: 700; font-size: 1.1rem; color: #0F172A; margin-bottom: 0.35rem;">
                ⚡ Generate a New Preparation Sprint
            </div>
            <div style="font-size: 0.85rem; color: #64748B; margin-bottom: 1.25rem;">
                Select your timeline and target role to create a customized curriculum targeting your active gaps.
            </div>
        """, unsafe_allow_html=True)

        col_r1, col_r2, col_r3 = st.columns([2, 1.2, 1.3], vertical_alignment="bottom")

        with col_r1:
            plan_role = st.text_input(
                "Target Job Role:",
                value=user_record.get("target_role", "Software Development Engineer (SDE-1)")
            )

        with col_r2:
            duration_choice = st.selectbox(
                "Sprint Duration:",
                [7, 14, 30],
                index=1,
                format_func=lambda d: f"{d}-Day {'Sprint' if d==7 else ('Placement Plan' if d==14 else 'Comprehensive Track')}"
            )

        with col_r3:
            gen_btn = st.button("🚀 Generate Roadmap", type="primary", width="stretch")

        st.markdown("</div>", unsafe_allow_html=True)

    # Process roadmap generation
    if gen_btn:
        with st.spinner(f"Curating {duration_choice}-day personalized placement roadmap targeting your active weaknesses..."):
            svc = GeminiService()
            res = svc.generate_daywise_roadmap(
                role_title=plan_role,
                weaknesses=weaknesses,
                duration_days=duration_choice
            )
            daily_tasks = res.get("daily_plan", [])
            weak_names = ", ".join([w.get("topic_name", "") for w in weaknesses[:4]])

            # Save in SQLite
            new_rm_id = save_roadmap_with_tasks(
                user_id=user_id,
                title=res.get("title", f"{duration_choice}-Day Sprint for {plan_role}"),
                target_role=plan_role,
                duration_days=duration_choice,
                weak_topics_covered=weak_names,
                plan_content=res.get("overview", ""),
                daily_tasks=daily_tasks
            )
            st.session_state["active_roadmap_id"] = new_rm_id
            st.success(f"Roadmap generated and saved! ({len(daily_tasks)} daily tasks)")
            st.rerun()

    # 2. Existing Roadmaps
    saved_roadmaps = get_user_roadmaps(user_id)

    if not saved_roadmaps:
        st.info(
            "💡 **No active preparation roadmap yet:** Configure your target role and sprint duration above, "
            "then click **Generate Roadmap** to build your interactive study schedule.",
            icon="ℹ️"
        )
        return

    # Select Active Roadmap
    active_rm_id = st.session_state.get("active_roadmap_id", saved_roadmaps[0]["id"])
    rm_map = {f"{r['title']} ({r.get('progress_percent', 0)}% done) • {str(r.get('created_at', ''))[:10]}": r["id"] for r in saved_roadmaps}

    # Find label matching active_rm_id
    default_idx = 0
    for idx, (lbl, r_id) in enumerate(rm_map.items()):
        if r_id == active_rm_id:
            default_idx = idx
            break

    col_pick, col_del = st.columns([3, 1], vertical_alignment="bottom")
    with col_pick:
        selected_rm_lbl = st.selectbox("Select Active Study Roadmap:", options=list(rm_map.keys()), index=default_idx)
        active_rm_id = rm_map[selected_rm_lbl]
        st.session_state["active_roadmap_id"] = active_rm_id

    with col_del:
        if st.button("🗑️ Delete Roadmap", width="stretch", help="Permanently deletes selected roadmap"):
            delete_roadmap(active_rm_id, user_id)
            if "active_roadmap_id" in st.session_state:
                del st.session_state["active_roadmap_id"]
            st.success("Roadmap deleted.")
            st.rerun()

    # Load complete active roadmap with tasks
    active_rm = get_roadmap_by_id(active_rm_id, user_id)
    if not active_rm:
        st.warning("Selected roadmap not found.")
        return

    # 3. Roadmap Header & Progress
    progress_pct = active_rm.get("progress_percent", 0)
    tasks = active_rm.get("tasks", [])
    completed_count = sum(1 for t in tasks if t.get("is_completed"))

    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 14px rgba(15, 23, 42, 0.03);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 8px;">
            <div>
                <span style="font-size: 0.75rem; font-weight: 700; color: #4F46E5; text-transform: uppercase; letter-spacing: 0.05em;">Active Curriculum</span>
                <h3 style="margin: 4px 0 2px 0; color: #0F172A; font-size: 1.25rem;">{active_rm['title']}</h3>
                <span style="font-size: 0.8rem; color: #64748B;">Target: {active_rm.get('target_role', '')} • {active_rm.get('duration_days', 14)} Days • Created {str(active_rm.get('created_at', ''))[:10]}</span>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Completion</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: #4F46E5;">{progress_pct}%</div>
            </div>
        </div>
        <div style="font-size: 0.88rem; color: #334155; line-height: 1.5; margin-bottom: 10px;">
            {active_rm.get('plan_content', '')}
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #64748B; margin-bottom: 4px;">
            <span>Tasks Completed: <b>{completed_count}</b> of <b>{len(tasks)}</b></span>
            <span>{len(tasks) - completed_count} remaining</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.progress(progress_pct / 100.0)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # 4. Interactive Daily Task List
    st.markdown("### 📋 Daily Learning Goals & Practical Tasks")
    st.caption("Check off items as you complete them. Your progress is saved automatically to your profile.")

    for task in tasks:
        t_id = task["id"]
        day_num = task["day_number"]
        topic = task["focus_topic"]
        concept = task["core_concept"]
        study = task["recommended_study"]
        exercise = task["practical_exercise"]
        hours = task["hours_recommended"]
        is_done = bool(task["is_completed"])

        with st.container():
            col_check, col_content = st.columns([0.4, 6], vertical_alignment="top")

            with col_check:
                # Checkbox toggling updates SQLite
                checked = st.checkbox(
                    f"Day {day_num} done",
                    value=is_done,
                    key=f"task_check_{t_id}",
                    label_visibility="collapsed"
                )
                if checked != is_done:
                    toggle_roadmap_task(t_id, checked)
                    st.rerun()

            with col_content:
                st_decor = "text-decoration: line-through; opacity: 0.65;" if is_done else ""
                bg_color = "#F8FAFC" if is_done else "#FFFFFF"
                border_color = "#E2E8F0" if is_done else "#CBD5E1"

                st.markdown(f"""
                <div style="background: {bg_color}; border: 1px solid {border_color}; border-radius: 12px; padding: 1.1rem; margin-bottom: 0.75rem; {st_decor}">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="font-weight: 700; color: #0F172A; font-size: 0.95rem;">
                            Day {day_num}: {topic}
                        </span>
                        <span style="background: #EEF2FF; color: #4338CA; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 6px;">
                            ⏱️ {hours} Hours
                        </span>
                    </div>
                    <div style="font-size: 0.85rem; color: #475569; margin-top: 4px; line-height: 1.45;">
                        <b>Core Concept:</b> {concept}
                    </div>
                    <div style="font-size: 0.82rem; color: #334155; margin-top: 4px; line-height: 1.45;">
                        <b>Recommended Study:</b> {study}
                    </div>
                    <div style="font-size: 0.82rem; color: #0F766E; margin-top: 4px; line-height: 1.45; background: #F0FDFA; padding: 6px 10px; border-radius: 8px;">
                        <b>Practical Coding Exercise:</b> {exercise}
                    </div>
                </div>
                """, unsafe_allow_html=True)
