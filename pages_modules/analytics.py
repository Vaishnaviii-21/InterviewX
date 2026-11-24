"""
Progress Analytics module for InterviewX.
Visualizes long-term candidate interview trajectories using Plotly:
- Score improvement progression over time
- Competency distribution across assessment pillars
- Category distribution (Technical vs HR vs Behavioral vs Coding)
- Most improved skills and frequent technical misconceptions
- Purely database-driven analytics with empty-state handling
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from auth import get_current_user, is_authenticated
from database import get_user_analytics, get_all_interviews
from components.charts import render_score_trend_chart, render_competency_pie_chart

def render_analytics_page():
    """Renders the comprehensive performance analytics dashboard."""
    st.markdown("## 📈 Progress Analytics & Performance Trends")
    st.markdown(
        "Track your quantitative interview trajectory over time. Measure accuracy gains, "
        "analyze category distributions, and monitor how close you are to placement readiness."
    )

    logged_in = is_authenticated()
    curr_user = get_current_user()
    user_id = curr_user["id"] if (logged_in and curr_user) else 1

    analytics = get_user_analytics(user_id=user_id)
    total_interviews = analytics.get("total_interviews", 0)

    # Empty state for new users
    if total_interviews == 0:
        st.info(
            "📊 **Not enough interview records for analytics:** Complete at least one mock interview "
            "to populate your progress curves, competency breakdowns, and weakness distribution.",
            icon="ℹ️"
        )
        if st.button("🎙️ Start Your First Mock Interview", type="primary"):
            st.session_state["active_page"] = "interview"
            st.rerun()
        return

    # 1. KPI Metric Bar
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        st.metric("Total Interviews", total_interviews)
    with col_k2:
        st.metric("Average Score", f"{analytics.get('avg_overall', 0.0):.1f}%")
    with col_k3:
        st.metric("Highest Score", f"{analytics.get('highest_score', 0.0):.1f}%")
    with col_k4:
        readiness = analytics.get("readiness_index", 0)
        st.metric("Placement Readiness", f"{readiness}%")

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # 2. Main Visual Charts Row (Trendline + Category Distribution)
    col_trend, col_pie = st.columns([1.35, 1], vertical_alignment="top")

    with col_trend:
        st.markdown("#### 📈 Score Progression Over Time")
        st.caption("Tracking overall score and technical accuracy across your completed sessions.")
        trend_fig = render_score_trend_chart(analytics.get("score_trends", []))
        st.plotly_chart(trend_fig, width="stretch")

    with col_pie:
        st.markdown("#### 🥧 Competency Performance Breakdown")
        st.caption("Distribution of average candidate evaluation scores across core pillars.")
        pie_fig = render_competency_pie_chart(analytics)
        st.plotly_chart(pie_fig, width="stretch")

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # 3. Interview Rounds Distribution & Competency Bar
    interviews = get_all_interviews(user_id=user_id, limit=50)
    col_cat, col_comp = st.columns(2)

    with col_cat:
        st.markdown("#### 🔀 Interview Category Distribution")
        st.caption("Types of interview rounds completed.")
        type_counts = {}
        for i in interviews:
            t = i.get("interview_type", "Technical")
            type_counts[t] = type_counts.get(t, 0) + 1

        donut_fig = go.Figure(data=[go.Pie(
            labels=list(type_counts.keys()),
            values=list(type_counts.values()),
            hole=0.45,
            marker=dict(colors=["#4F46E5", "#0EA5E9", "#10B981", "#F59E0B", "#8B5CF6"], line=dict(color="#FFFFFF", width=2)),
            textinfo="label+percent",
            textposition="auto",
            hovertemplate="<b>%{label}</b><br>Sessions: %{value}<br>Share: %{percent}<extra></extra>"
        )])
        donut_fig.update_layout(
            height=280,
            margin=dict(l=20, r=20, t=25, b=20),
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(donut_fig, width="stretch")

    with col_comp:
        st.markdown("#### 📊 Evaluation Pillar Comparison")
        st.caption("Average scores vs 75% placement readiness threshold.")
        p_names = ["Accuracy", "Relevance", "Completeness", "Clarity"]
        p_vals = [
            analytics.get("avg_accuracy", 0.0),
            analytics.get("avg_relevance", 0.0),
            analytics.get("avg_completeness", 0.0),
            analytics.get("avg_clarity", 0.0)
        ]
        bar_fig = go.Figure(data=[go.Bar(
            x=p_names,
            y=p_vals,
            marker=dict(color=["#4F46E5", "#0EA5E9", "#10B981", "#F59E0B"], line=dict(color="#FFFFFF", width=1.5)),
            text=[f"{v:.1f}%" for v in p_vals],
            textposition="auto",
            textfont=dict(family="Plus Jakarta Sans", size=11, color="#FFFFFF"),
            hovertemplate="<b>%{x}</b>: %{y:.1f}%<extra></extra>"
        )])
        bar_fig.add_hline(
            y=75,
            line_dash="dot",
            line_color="#10B981",
            annotation_text="75% Target Benchmark",
            annotation_position="top left",
            annotation_font=dict(size=10, color="#10B981", family="Plus Jakarta Sans")
        )
        bar_fig.update_layout(
            height=280,
            margin=dict(l=20, r=20, t=25, b=20),
            yaxis=dict(range=[0, 105], ticksuffix="%"),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Plus Jakarta Sans, sans-serif", color="#334155")
        )
        st.plotly_chart(bar_fig, width="stretch")

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # 4. Strengths & Recurring Weaknesses Breakdown
    col_w, col_s = st.columns(2)
    with col_w:
        st.markdown("#### ⚠️ Top Recurring Technical Weaknesses")
        weaknesses = analytics.get("weaknesses", [])
        if weaknesses:
            for w in weaknesses:
                st.markdown(f"""
                <div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.5rem;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-weight: 700; color: #991B1B; font-size: 0.88rem;">⚠️ {w['topic_name']}</span>
                        <span style="font-size: 0.75rem; background: #FEE2E2; color: #991B1B; font-weight: 700; padding: 1px 6px; border-radius: 6px;">Flagged {w['frequency']}x</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #7F1D1D; margin-top: 3px;"><i>{w.get('notes', '')}</i></div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("No recurring weaknesses detected.")

    with col_s:
        st.markdown("#### 🏆 Confirmed Technical Strengths")
        strengths = analytics.get("strengths", [])
        if strengths:
            for s in strengths:
                st.markdown(f"""
                <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.5rem;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-weight: 700; color: #166534; font-size: 0.88rem;">✅ {s['topic_name']}</span>
                        <span style="font-size: 0.75rem; background: #DCFCE7; color: #15803D; font-weight: 700; padding: 1px 6px; border-radius: 6px;">Verified {s['frequency']}x</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #14532D; margin-top: 3px;"><i>{s.get('notes', '')}</i></div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("No verified strengths detected yet.")
