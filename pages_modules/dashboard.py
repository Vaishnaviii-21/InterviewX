"""
Dashboard module for InterviewX.
Displays key performance indicators, score trends, competency pie breakdown,
recurring weaknesses, strengths, and recent interview reports with clean layout alignment.
"""

import html
import json
import textwrap
import streamlit as st
import pandas as pd
from services.analytics_service import AnalyticsService
from components.cards import render_metric_card, render_honest_feedback_comparison
from components.charts import render_score_trend_chart, render_competency_pie_chart
from database.models import get_interview_questions, update_user_profile, get_user_by_id
from auth import get_current_user, is_authenticated, logout_user, render_auth_guard

def render_dashboard():
    """Renders the comprehensive candidate analytics dashboard."""
    if not render_auth_guard("the Candidate Dashboard"):
        return

    curr_user = get_current_user()
    user_id = curr_user["id"]

    # Top Navigation / Utility Row with Clear Logout Button
    head_col1, head_col2 = st.columns([3, 1], vertical_alignment="center")
    with head_col1:
        st.markdown('<h1 id="main-content" class="page-title-h1" tabindex="-1"><span aria-hidden="true">📊</span> Candidate Dashboard</h1>', unsafe_allow_html=True)
    with head_col2:
        if st.button("🚪 Logout", key="dash_logout_btn", width="stretch", help="Sign out of your account"):
            logout_user()
            st.toast("Logged out successfully.")
            st.rerun()

    data = AnalyticsService.get_dashboard_summary(user_id=user_id)
    user = data["user"]
    metrics = data["metrics"]
    readiness_label = data["readiness_label"]
    readiness_color = data["readiness_color"]
    readiness_desc = data["readiness_desc"]
    score_delta = data["score_delta"]
    recent_interviews = data["recent_interviews"]

    # 1. Unified Profile Header Banner (Securely escaped & accessible)
    user_initial = (user.get("name") or "C")[0].upper()
    user_name = user.get("name", "Candidate")
    user_role = user.get("target_role", "Software Development Engineer (SDE-1)")
    user_college = user.get("college", "National Institute of Technology")
    user_grad = user.get("graduation_year", 2026)
    readiness_score = metrics.get("readiness_index", 0)

    clean_uinitial = html.escape(str(user_initial))
    clean_uname = html.escape(str(user_name))
    clean_urole = html.escape(str(user_role))
    clean_ucollege = html.escape(str(user_college))
    clean_rlabel = html.escape(str(readiness_label))

    profile_html = textwrap.dedent(f"""\
<div class="profile-banner" role="region" aria-label="Candidate Profile Summary">
<div class="profile-left">
<div class="profile-avatar" aria-hidden="true">{clean_uinitial}</div>
<div class="profile-info">
<h2 class="profile-greeting">Welcome back, <span class="profile-name">{clean_uname}</span></h2>
<div class="profile-meta-row">
<span><span aria-hidden="true">🎯</span> Target: <b class="profile-role-tag">{clean_urole}</b></span>
<span class="profile-meta-separator" aria-hidden="true">•</span>
<span><span aria-hidden="true">🎓</span> {clean_ucollege}</span>
<span class="profile-meta-separator" aria-hidden="true">•</span>
<span>Class of {user_grad}</span>
</div>
</div>
</div>
<div class="profile-right">
<div class="readiness-pill-box">
<div class="readiness-tag">Campus Placement Readiness</div>
<div class="readiness-status-row">
<span class="status-indicator-dot" style="background-color: {readiness_color};" aria-hidden="true"></span>
<span class="sr-only">Readiness Status: {clean_rlabel} ({readiness_score}%)</span>
<span class="readiness-score-number" style="color: {readiness_color};" aria-label="Readiness Score: {readiness_score} percent">{readiness_score}%</span>
<span class="readiness-label-badge">{clean_rlabel}</span>
</div>
</div>
</div>
</div>""").strip()

    st.markdown(profile_html, unsafe_allow_html=True)

    # 2. Quick Launch Action Bar
    q_col1, q_col2, q_col3, q_col4 = st.columns(4, vertical_alignment="center")
    with q_col1:
        if st.button("🎙️ Start Mock Interview", type="primary", width="stretch"):
            st.session_state["active_page"] = "interview"
            st.rerun()
    with q_col2:
        if st.button("📄 Resume Analyzer", width="stretch"):
            st.session_state["active_page"] = "resume_analyzer"
            st.rerun()
    with q_col3:
        if st.button("🗺️ Study Roadmap", width="stretch"):
            st.session_state["active_page"] = "roadmap"
            st.rerun()
    with q_col4:
        if st.button("⚠️ Weakness Tracker", width="stretch"):
            st.session_state["active_page"] = "weakness_tracker"
            st.rerun()

    st.markdown('<div class="dashboard-spacer-sm"></div>', unsafe_allow_html=True)

    # 3. Four Key Performance Metric Cards (Synchronized Heights & Baseline)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        delta_str = f"{score_delta}%" if score_delta is not None else None
        is_pos = (score_delta >= 0) if score_delta is not None else True
        render_metric_card(
            label="Avg Interview Score",
            value=f"{metrics.get('avg_overall', 0.0)}%",
            delta=delta_str,
            delta_positive=is_pos,
            subtitle="Across completed sessions",
            icon="🎯"
        )
    with kpi2:
        render_metric_card(
            label="Mocks Completed",
            value=str(metrics.get("total_interviews", 0)),
            subtitle="Persistent SQLite sessions",
            icon="📝"
        )
    with kpi3:
        render_metric_card(
            label="Questions Evaluated",
            value=str(metrics.get("total_questions", 0)),
            subtitle="Strict technical critiques",
            icon="❓"
        )
    with kpi4:
        render_metric_card(
            label="Technical Accuracy",
            value=f"{metrics.get('avg_accuracy', 0.0)}%",
            subtitle="Factual correctness rate",
            icon="⚡"
        )

    st.markdown('<div class="dashboard-spacer"></div>', unsafe_allow_html=True)

    # 4. Visual Performance Analytics (Synchronized Trendline & Competency Pie Chart)
    col_trend, col_pie = st.columns([1.25, 1], vertical_alignment="top")
    
    with col_trend:
        st.markdown("#### 📈 Performance Trendline")
        st.caption("Overall interview score progression vs 75% campus placement target benchmark.")
        trend_trends = metrics.get("score_trends", [])
        trend_fig = render_score_trend_chart(trend_trends)
        st.plotly_chart(trend_fig, width="stretch", config={"displayModeBar": False, "responsive": True})
        if trend_trends:
            latest_s = trend_trends[-1].get("overall_score", 0.0)
            st.markdown(f'<div class="sr-only">Performance Trend: {len(trend_trends)} session(s) completed. Most recent score is {latest_s:.1f} percent against target benchmark of 75 percent.</div>', unsafe_allow_html=True)

    with col_pie:
        st.markdown("#### 🥧 Competency Performance Breakdown")
        st.caption("Candidate's actual evaluation scores across the 4 core competency pillars.")
        pie_fig = render_competency_pie_chart(metrics)
        st.plotly_chart(pie_fig, width="stretch", config={"displayModeBar": False, "responsive": True})
        acc_val = float(metrics.get("avg_accuracy", 0.0))
        rel_val = float(metrics.get("avg_relevance", 0.0))
        comp_val = float(metrics.get("avg_completeness", 0.0))
        clar_val = float(metrics.get("avg_clarity", 0.0))
        st.markdown(
            f'<div class="sr-only">Competency Pillar Breakdown: Technical Accuracy {acc_val:.1f}%, Relevance {rel_val:.1f}%, Completeness {comp_val:.1f}%, Clarity &amp; Communication {clar_val:.1f}%.</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="dashboard-spacer"></div>', unsafe_allow_html=True)

    # 5. Recurring Weaknesses and Technical Strengths
    col_weak, col_str = st.columns(2)
    
    with col_weak:
        st.markdown("#### ⚠️ Recurring Weaknesses Identified")
        st.caption("Concepts where misconceptions or incomplete answers were repeatedly detected.")
        weaknesses = metrics.get("weaknesses", [])
        if weaknesses:
            for w in weaknesses:
                w_topic = html.escape(str(w.get('topic_name', 'Topic')))
                w_notes = html.escape(str(w.get('notes', '')))
                w_freq = int(w.get('frequency', 1))
                w_html = textwrap.dedent(f"""\
<div class="topic-card-weak" role="region" aria-label="Weakness: {w_topic}">
<div style="display: flex; justify-content: space-between; align-items: center;">
<span style="font-weight: 700; color: #991B1B; font-size: 0.9rem;">
<span aria-hidden="true">❌</span> {w_topic}
</span>
<span style="background: #FEE2E2; color: #991B1B; font-size: 0.75rem; font-weight: 700; padding: 2px 8px; border-radius: 6px;">
Flagged {w_freq}x
</span>
</div>
<div style="font-size: 0.8rem; color: #7F1D1D; margin-top: 5px; line-height: 1.45;">
{w_notes}
</div>
</div>""").strip()
                st.markdown(w_html, unsafe_allow_html=True)
        else:
            st.info("No recurring weaknesses recorded yet. Complete more mock interviews to detect gaps.")

    with col_str:
        st.markdown("#### 🏆 Confirmed Technical Strengths")
        st.caption("Areas where your answers demonstrated solid depth, accurate syntax, and clarity.")
        strengths = metrics.get("strengths", [])
        if strengths:
            for s in strengths:
                s_topic = html.escape(str(s.get('topic_name', 'Topic')))
                s_notes = html.escape(str(s.get('notes', '')))
                s_freq = int(s.get('frequency', 1))
                s_html = textwrap.dedent(f"""\
<div class="topic-card-strength" role="region" aria-label="Strength: {s_topic}">
<div style="display: flex; justify-content: space-between; align-items: center;">
<span style="font-weight: 700; color: #065F46; font-size: 0.9rem;">
<span aria-hidden="true">✅</span> {s_topic}
</span>
<span style="background: #D1FAE5; color: #065F46; font-size: 0.75rem; font-weight: 700; padding: 2px 8px; border-radius: 6px;">
Verified {s_freq}x
</span>
</div>
<div style="font-size: 0.8rem; color: #064E3B; margin-top: 5px; line-height: 1.45;">
{s_notes}
</div>
</div>""").strip()
                st.markdown(s_html, unsafe_allow_html=True)
        else:
            st.info("No confirmed strengths recorded yet.")

    st.markdown('<div class="dashboard-spacer"></div>', unsafe_allow_html=True)

    # 6. Recent Mock Interview Sessions & Detailed Reports
    st.markdown("### 📋 Recent Mock Interview Sessions")
    st.caption("Click any session below to inspect the detailed questions, candidate answers, and honest critiques.")

    if not recent_interviews:
        st.info("No past mock interviews found. Start your first session using the button above!")
    else:
        for interview in recent_interviews:
            score = interview.get("overall_score", 0.0)
            score_color = "#10B981" if score >= 75 else ("#F59E0B" if score >= 60 else "#EF4444")
            
            expander_title = (
                f"Session #{interview['id']}: {interview['role_title']} "
                f"• Score: {score:.1f}% • {interview['difficulty']} "
                f"• {str(interview['created_at'])[:10]}"
            )
            
            with st.expander(expander_title):
                summary_html = textwrap.dedent(f"""\
<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.15rem; margin-bottom: 1rem;">
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
<div>
<span style="font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Interview Type:</span>
<span style="font-weight: 600; color: #0F172A; font-size: 0.88rem;"> {interview.get('interview_type', 'Technical')}</span>
</div>
<div>
<span style="font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Target Track:</span>
<span style="font-weight: 600; color: #0F172A; font-size: 0.88rem;"> {interview.get('target_company_track', 'General')}</span>
</div>
<div>
<span style="font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Overall Score:</span>
<span style="font-weight: 800; color: {score_color}; font-size: 1.05rem;"> {score:.1f}%</span>
</div>
</div>
<div style="margin-top: 0.75rem; font-size: 0.875rem; color: #334155; line-height: 1.5; border-top: 1px solid #E2E8F0; padding-top: 0.75rem;">
<b>Executive Summary:</b> {interview.get('summary', 'No summary recorded.')}
</div>
</div>""").strip()
                st.markdown(summary_html, unsafe_allow_html=True)

                if st.button(f"📋 Open Full Feedback Report & PDF (Session #{interview['id']})", key=f"dash_report_{interview['id']}", type="secondary"):
                    st.session_state["view_session_id"] = interview["id"]
                    st.session_state["active_page"] = "feedback"
                    st.rerun()

                # Fetch detailed questions for this session from SQLite
                questions = get_interview_questions(interview["id"])
                if questions:
                    st.markdown("##### 🔍 Questions & Honest Evaluations:")
                    for q in questions:
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
                            question=q["question_text"],
                            user_answer=q["user_answer"],
                            honest_critique=q["honest_feedback"],
                            incorrect_concepts=incorrect,
                            missing_info=missing,
                            improved_answer=q["improved_answer"],
                            why_better=q["improvement_reason"]
                        )
                else:
                    st.caption("No individual question evaluations logged for this session.")
