"""
Module 5: Progress Tracker & Full History for InterviewX.
Displays historical interview attempts, question-level audits, score comparisons,
and allows viewing full feedback reports or deleting session records with strict user isolation.
"""

import json
import streamlit as st
import pandas as pd
from auth import get_current_user, is_authenticated, render_auth_guard
from database import (
    get_all_interviews,
    get_interview_questions,
    delete_interview_session
)
from components.cards import render_honest_feedback_comparison

def render_history_page():
    """Renders the comprehensive interview history and progress tracker."""
    if not render_auth_guard("Interview History & Archive"):
        return

    st.markdown('<h1 id="main-content" class="page-title-h1" tabindex="-1"><span aria-hidden="true">📁</span> Interview History &amp; Archive</h1>', unsafe_allow_html=True)
    st.markdown(
        "Audit every mock interview attempt. Track your long-term score progression, "
        "measure accuracy improvements, review question-level evaluations, or export reports."
    )

    curr_user = get_current_user()
    user_id = curr_user["id"]

    interviews = get_all_interviews(user_id=user_id, limit=50)

    if not interviews:
        st.info("No mock interviews recorded yet for your account.", icon="ℹ️")
        if st.button("🎙️ Start Your First Mock Interview", type="primary"):
            st.session_state["active_page"] = "interview"
            st.rerun()
        return

    # 1. Summary Metrics
    scores = [i.get("overall_score", 0) for i in interviews]
    avg_score = sum(scores) / len(scores) if scores else 0
    max_score = max(scores) if scores else 0
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Total Sessions", len(interviews))
    with col_m2:
        st.metric("Average Score", f"{avg_score:.1f}%")
    with col_m3:
        st.metric("Highest Score", f"{max_score:.1f}%")
    with col_m4:
        most_recent = str(interviews[0].get("created_at", "N/A"))[:10]
        st.metric("Latest Session", most_recent)

    st.markdown("---")

    # 2. Sessions Table
    st.markdown("### 📋 Completed Interview Sessions")
    records = []
    for i in interviews:
        records.append({
            "Session ID": f"#{i['id']}",
            "Job Role": i.get("role_title", "General"),
            "Difficulty": (i.get("difficulty") or "Medium").capitalize(),
            "Category": i.get("interview_type", "Comprehensive"),
            "Overall Score": f"{i.get('overall_score', 0):.1f}%",
            "Accuracy": f"{i.get('accuracy_score', 0):.1f}%",
            "Date": str(i.get("created_at", ""))[:16],
            "raw_id": i["id"]
        })
    df = pd.DataFrame(records)
    display_df = df.drop(columns=["raw_id"])
    st.dataframe(display_df, width="stretch", hide_index=True)

    st.markdown("---")

    # 3. Detailed Session Inspector
    st.markdown("### 🔍 Detailed Session Inspector & Actions")
    session_options = {
        f"Session #{i['id']} • {i['role_title']} ({i['overall_score']:.1f}%) • {str(i['created_at'])[:10]}": i["id"]
        for i in interviews
    }
    
    selected_label = st.selectbox("Select Session to Inspect:", list(session_options.keys()))
    selected_id = session_options[selected_label]

    col_btn1, col_btn2 = st.columns([2, 1])
    with col_btn1:
        if st.button("📋 Open Full Feedback Report & Download PDF", type="primary", width="stretch"):
            st.session_state["view_session_id"] = selected_id
            st.session_state["active_page"] = "feedback"
            st.rerun()

    with col_btn2:
        with st.expander("🗑️ Delete Session"):
            st.caption("Permanently delete this interview session and its questions.")
            confirm_del = st.checkbox("Confirm deletion", key=f"del_confirm_{selected_id}")
            if st.button("Delete Permanently", type="secondary", disabled=not confirm_del, width="stretch"):
                success = delete_interview_session(selected_id, user_id=user_id)
                if success:
                    st.success(f"Session #{selected_id} deleted successfully.")
                    st.rerun()
                else:
                    st.error("Failed to delete session.")

    # Questions Preview Accordion
    questions = get_interview_questions(selected_id)
    if questions:
        st.markdown(f"#### Question Evaluations ({len(questions)} Questions):")
        for idx, q in enumerate(questions, 1):
            with st.expander(f"Q{idx}: {q.get('question_text', 'Question')[:80]}... (Score: {q.get('score', 0):.1f}/10)"):
                incorrect = []
                missing = []
                try:
                    if q.get("incorrect_concepts"):
                        incorrect = json.loads(q["incorrect_concepts"])
                except Exception:
                    incorrect = [q["incorrect_concepts"]]

                try:
                    if q.get("missing_information"):
                        missing = json.loads(q["missing_information"])
                except Exception:
                    missing = [q["missing_information"]]

                render_honest_feedback_comparison(
                    question=q.get("question_text", ""),
                    user_answer=q.get("user_answer", ""),
                    honest_critique=q.get("honest_feedback", ""),
                    incorrect_concepts=incorrect,
                    missing_info=missing,
                    improved_answer=q.get("improved_answer", ""),
                    why_better=q.get("improvement_reason", "")
                )
    else:
        st.caption("No question-level records found for this session.")
