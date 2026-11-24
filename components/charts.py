"""
Plotly charting components for InterviewX performance indicators and analytics.
Clean, modern aesthetics with consistent typography and synchronized heights.
"""

from typing import List, Dict, Any
import plotly.graph_objects as go
import pandas as pd

def render_score_trend_chart(trends: List[Dict[str, Any]]) -> go.Figure:
    """
    Renders an interactive line chart showing interview score progress over time,
    with a benchmark reference line for campus placement readiness.
    Synchronized to 340px height for dashboard alignment.
    """
    if not trends:
        # Empty placeholder figure
        fig = go.Figure()
        fig.add_annotation(
            text="No interview sessions recorded yet.<br>Complete your first mock to see your trendline!",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#64748B", family="Plus Jakarta Sans")
        )
        fig.update_layout(
            height=340,
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=20, b=20)
        )
        return fig

    df = pd.DataFrame(trends)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df = df.sort_values("created_at")

    fig = go.Figure()

    # Campus placement readiness target area / benchmark
    fig.add_hline(
        y=75,
        line_dash="dot",
        line_color="#10B981",
        line_width=1.5,
        annotation_text="Target: Placement Ready (75%+)",
        annotation_position="top left",
        annotation_font=dict(size=11, color="#10B981", family="Plus Jakarta Sans")
    )

    # Actual candidate overall scores
    fig.add_trace(go.Scatter(
        x=df["created_at"],
        y=df["overall_score"],
        mode="lines+markers",
        name="Overall Score",
        line=dict(color="#4F46E5", width=3, shape="spline"),
        marker=dict(size=8, color="#4F46E5", line=dict(width=2, color="#FFFFFF")),
        hovertemplate="<b>%{customdata[0]}</b><br>Score: <b>%{y:.1f}%</b><br>Difficulty: %{customdata[1]}<br>Date: %{x|%b %d, %Y}<extra></extra>",
        customdata=df[["role_title", "difficulty"]].values
    ))

    # Accuracy line
    fig.add_trace(go.Scatter(
        x=df["created_at"],
        y=df["accuracy_score"],
        mode="lines",
        name="Technical Accuracy",
        line=dict(color="#0EA5E9", width=2, dash="dash"),
        hovertemplate="Technical Accuracy: <b>%{y:.1f}%</b><extra></extra>"
    ))

    fig.update_layout(
        height=360,
        margin=dict(l=35, r=25, t=40, b=30),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#334155"),
        hoverlabel=dict(bgcolor="#1E1B4B", font_size=12, font_color="#FFFFFF"),
        xaxis=dict(
            showgrid=True,
            gridcolor="#F1F5F9",
            zeroline=False,
            title=None
        ),
        yaxis=dict(
            range=[0, 105],
            showgrid=True,
            gridcolor="#F1F5F9",
            zeroline=False,
            ticksuffix="%",
            title=None
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11)
        )
    )

    return fig

def render_competency_pie_chart(metrics: Dict[str, Any]) -> go.Figure:
    """
    Renders a clean, professional pie chart titled 'Competency Performance Breakdown'
    displaying candidate's actual evaluation scores across the 4 core assessment pillars:
    - Technical Accuracy
    - Relevance
    - Completeness
    - Clarity & Communication
    Synchronized to 360px height for dashboard alignment.
    """
    labels = [
        "Technical Accuracy",
        "Relevance",
        "Completeness",
        "Clarity & Communication"
    ]
    # Extract candidate's actual evaluation scores (supports both aggregated & session dicts)
    values = [
        float(metrics.get("avg_accuracy", metrics.get("accuracy_score", 0.0))),
        float(metrics.get("avg_relevance", metrics.get("relevance_score", 0.0))),
        float(metrics.get("avg_completeness", metrics.get("completeness_score", 0.0))),
        float(metrics.get("avg_clarity", metrics.get("clarity_score", 0.0)))
    ]

    # Professional color palette consistent with InterviewX brand identity
    colors = [
        "#4F46E5",  # Technical Accuracy (Brand Indigo)
        "#0EA5E9",  # Relevance (Vibrant Sky Blue)
        "#10B981",  # Completeness (Emerald Green)
        "#F59E0B"   # Clarity & Communication (Warm Amber)
    ]

    # Empty placeholder when no interview scores have been recorded yet
    if sum(values) <= 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No evaluation data recorded yet.<br>Complete your first mock interview to see your competency breakdown!",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=13, color="#64748B", family="Plus Jakarta Sans, sans-serif")
        )
        fig.update_layout(
            height=360,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=20, b=20)
        )
        return fig

    fig = go.Figure()

    fig.add_trace(go.Pie(
        labels=labels,
        values=values,
        hole=0,
        marker=dict(
            colors=colors,
            line=dict(color="#FFFFFF", width=2.5)
        ),
        textinfo="label+percent",
        textposition="auto",
        insidetextorientation="horizontal",
        insidetextfont=dict(size=11, family="Plus Jakarta Sans, sans-serif", color="#FFFFFF"),
        outsidetextfont=dict(size=11, family="Plus Jakarta Sans, sans-serif", color="#0F172A"),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Evaluation Score: <b>%{value:.1f}%</b><br>"
            "Competency Share: <b>%{percent}</b>"
            "<extra></extra>"
        ),
        sort=False
    ))

    fig.update_layout(
        height=360,
        margin=dict(l=35, r=35, t=35, b=25),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=11, family="Plus Jakarta Sans, sans-serif", color="#475569")
        ),
        hoverlabel=dict(
            bgcolor="#0F172A",
            font_size=12,
            font_family="Plus Jakarta Sans, sans-serif",
            font_color="#FFFFFF"
        ),
        paper_bgcolor="rgba(0,0,0,0)"
    )

    return fig
