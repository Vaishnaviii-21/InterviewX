"""
Post-Interview Feedback Report module for InterviewX.
Displays comprehensive performance reports after completed mock interviews:
- Overall score and placement readiness index
- 4 category scores (Accuracy, Conceptual, Communication, Relevance) with Bar visualizer
- Question-by-question analysis with honest critiques and exemplary sample answers
- Downloadable PDF report generator
- Direct action hooks to study roadmaps and weakness tracker
"""

import json
import streamlit as st
import plotly.graph_objects as go
from auth import get_current_user, is_authenticated
from database import (
    get_all_interviews,
    get_interview_by_id,
    get_interview_questions,
    get_user_by_id
)
from components.cards import render_honest_feedback_comparison
from utils.pdf_generator import PDFReportGenerator

def render_feedback_page():
    """Renders the comprehensive Post-Interview Feedback Report."""
    st.markdown("## 📋 Post-Interview Feedback Report")
    st.markdown(
        "Audit your interview performance with uncompromising engineering rigor. Review your score breakdown, "
        "identify technical misconceptions, compare with Tier-1 sample answers, and download your full PDF report."
    )

    logged_in = is_authenticated()
    curr_user = get_current_user()
    user_id = curr_user["id"] if (logged_in and curr_user) else 1
    user_record = get_user_by_id(user_id) or {"name": "Candidate"}

    # Fetch user sessions
    interviews = get_all_interviews(user_id=user_id, limit=30)
    if not interviews:
        st.info(
            "ℹ️ **No completed mock interviews found:** Start your first mock interview to generate your "
            "comprehensive performance report and honest critique.",
            icon="🎙️"
        )
        if st.button("🎙️ Start New Mock Interview", type="primary"):
            st.session_state["active_page"] = "interview"
            st.rerun()
        return

    # 1. Session Selector Header
    view_session_id = st.session_state.get("view_session_id")
    session_map = {
        f"Session #{i['id']} • {i['role_title']} ({i['overall_score']:.1f}%) • {str(i['created_at'])[:10]}": i["id"]
        for i in interviews
    }

    selected_label = list(session_map.keys())[0]
    if view_session_id:
        for lbl, s_id in session_map.items():
            if s_id == view_session_id:
                selected_label = lbl
                break

    col_sel, col_dl = st.columns([2.5, 1.2], vertical_alignment="bottom")
    with col_sel:
        active_label = st.selectbox(
            "Select Interview Session to Inspect:",
            options=list(session_map.keys()),
            index=list(session_map.keys()).index(selected_label)
        )
        selected_session_id = session_map[active_label]

    # Load session and questions from SQLite
    session = get_interview_by_id(selected_session_id)
    questions = get_interview_questions(selected_session_id)

    # PDF Download Button
    with col_dl:
        if session and questions:
            pdf_bytes = PDFReportGenerator.generate_interview_report_pdf(
                candidate_name=user_record.get("name", "Candidate"),
                session_data=session,
                questions_data=questions
            )
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_bytes,
                file_name=f"InterviewX_Report_Session_{selected_session_id}.pdf",
                mime="application/pdf",
                width="stretch"
            )

    if not session:
        st.error("Could not load session details.")
        return

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 2. Performance Summary Banner
    ovr = session.get("overall_score", 0.0)
    acc = session.get("accuracy_score", 0.0)
    conc = session.get("conceptual_score", acc)
    rel = session.get("relevance_score", 0.0)
    clar = session.get("clarity_score", 0.0)

    score_color = "#10B981" if ovr >= 75 else ("#F59E0B" if ovr >= 60 else "#EF4444")
    readiness = session.get("readiness_assessment", "Placement Ready" if ovr >= 75 else ("Needs Target Polish" if ovr >= 60 else "Early Prep Phase"))

    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 14px rgba(15, 23, 42, 0.03);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 12px;">
            <div>
                <span style="font-size: 0.75rem; font-weight: 700; color: #4F46E5; text-transform: uppercase; letter-spacing: 0.05em;">Session #{session['id']} Evaluation</span>
                <h2 style="margin: 4px 0 2px 0; color: #0F172A; font-size: 1.4rem;">{session.get('role_title', 'Software Engineer')}</h2>
                <span style="font-size: 0.85rem; color: #64748B;">{session.get('interview_type', 'Technical Round')} • {session.get('difficulty', 'Intermediate')} • {str(session.get('created_at', ''))[:16]}</span>
            </div>
            <div style="display: flex; gap: 15px; align-items: center;">
                <div style="text-align: right;">
                    <div style="font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Overall Score</div>
                    <div style="font-size: 2rem; font-weight: 800; color: {score_color}; line-height: 1.1;">{ovr:.1f}%</div>
                </div>
                <div style="background: {score_color}18; color: {score_color}; font-weight: 800; font-size: 0.82rem; padding: 6px 14px; border-radius: 20px; border: 1px solid {score_color}35;">
                    {readiness}
                </div>
            </div>
        </div>
        <div style="font-size: 0.9rem; color: #334155; line-height: 1.55; border-top: 1px solid #F1F5F9; padding-top: 12px;">
            <b>Executive Assessment:</b> {session.get('summary', 'No summary recorded.')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. Category Score Visualizer (Horizontal Bar Chart vs 75% Target)
    col_chart, col_action = st.columns([1.8, 1])

    with col_chart:
        st.markdown("#### 📊 Pillar Performance vs 75% Benchmark")
        categories = ["Technical Accuracy", "Conceptual Understanding", "Communication Skills", "Answer Relevance"]
        scores_list = [acc, conc, clar, rel]
        colors = ["#4F46E5", "#0EA5E9", "#10B981", "#F59E0B"]

        bar_fig = go.Figure()
        # Candidate Scores
        bar_fig.add_trace(go.Bar(
            y=categories,
            x=scores_list,
            orientation="h",
            marker=dict(color=colors, line=dict(color="#FFFFFF", width=1.5)),
            text=[f"{s:.1f}%" for s in scores_list],
            textposition="auto",
            textfont=dict(family="Plus Jakarta Sans", size=11, color="#FFFFFF"),
            name="Candidate Score",
            hovertemplate="<b>%{y}</b><br>Score: <b>%{x:.1f}%</b><extra></extra>"
        ))
        # Benchmark line at 75%
        bar_fig.add_vline(
            x=75,
            line_dash="dot",
            line_color="#EF4444",
            line_width=2,
            annotation_text="Placement Benchmark (75%)",
            annotation_position="top right",
            annotation_font=dict(size=10, color="#EF4444", family="Plus Jakarta Sans")
        )
        bar_fig.update_layout(
            height=260,
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis=dict(range=[0, 105], showgrid=True, gridcolor="#F1F5F9", ticksuffix="%"),
            yaxis=dict(autorange="reversed"),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Plus Jakarta Sans, sans-serif", color="#334155"),
            showlegend=False
        )
        st.plotly_chart(bar_fig, width="stretch")

    with col_action:
        st.markdown("#### 🎯 Next Actions")
        with st.container(border=True):
            st.markdown("**Ready to close your technical gaps?**")
            st.caption("Convert the weaknesses identified in this session into a day-by-day study roadmap.")
            if st.button("🗺️ Generate Sprint Roadmap", type="primary", width="stretch"):
                st.session_state["active_page"] = "roadmap"
                st.rerun()
            if st.button("🎙️ Start Another Mock", width="stretch"):
                st.session_state["active_page"] = "interview"
                st.rerun()

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # 4. Question-by-Question Detailed Evaluations
    st.markdown(f"### 🔍 Question-by-Question Deep Dive ({len(questions)} Questions)")
    st.caption("Inspect the interviewer's exact question, your submitted answer, detected misconceptions, and improved sample answers.")

    if not questions:
        st.info("No individual question evaluations found for this session.")
    else:
        for idx, q in enumerate(questions, 1):
            q_score = q.get("overall_score", 0.0)
            q_color = "#10B981" if q_score >= 75 else ("#F59E0B" if q_score >= 60 else "#EF4444")
            
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

            with st.expander(f"Question #{idx}: {q.get('question_text', '')[:70]}... (Score: {q_score:.1f}%)", expanded=(idx == 1)):
                st.markdown(f"""
                <div style="display: flex; gap: 15px; margin-bottom: 10px; font-size: 0.82rem; color: #64748B;">
                    <span><b>Category:</b> {q.get('category', 'Technical')}</span>
                    <span>• <b>Accuracy:</b> {q.get('accuracy_score', 0):.1f}%</span>
                    <span>• <b>Relevance:</b> {q.get('relevance_score', 0):.1f}%</span>
                    <span>• <b>Clarity:</b> {q.get('clarity_score', 0):.1f}%</span>
                </div>
                """, unsafe_allow_html=True)

                render_honest_feedback_comparison(
                    question=q["question_text"],
                    user_answer=q["user_answer"],
                    honest_critique=q["honest_feedback"],
                    incorrect_concepts=incorrect,
                    missing_info=missing,
                    improved_answer=q["improved_answer"],
                    why_better=q["improvement_reason"]
                )
