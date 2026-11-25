"""
Card and metric UI components for InterviewX.
Generates polished, accessible, responsive HTML cards and visual indicators
with clean Markdown rendering (no raw HTML leaks or markdown indentation bugs).
"""

import html
import re
import textwrap
from typing import List, Optional, Dict, Any
import streamlit as st

def sanitize_text(text: str) -> str:
    """
    Strips any stray raw HTML tags (e.g. <h3>, <p>, <div>, etc.) that might be returned
    by an LLM, question bank, or user input, and normalizes entities.
    """
    if not text:
        return ""
    # Strip any HTML tags
    cleaned = re.sub(r'<[^>]+>', '', str(text))
    # Unescape any HTML entities (&quot;, &amp;, etc.)
    cleaned = html.unescape(cleaned).strip()
    return cleaned

def render_metric_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    delta_positive: bool = True,
    subtitle: Optional[str] = None,
    icon: str = ""
):
    """
    Renders a modern metric card with consistent height, vertical alignment,
    and strict textwrap.dedent formatting to eliminate any raw HTML leaks.
    """
    if delta:
        arrow = "↑" if delta_positive else "↓"
        sr_direction = "Increased by" if delta_positive else "Decreased by"
        css_class = "delta-positive" if delta_positive else "delta-negative"
        delta_elem = f'<div class="metric-delta {css_class}"><span aria-hidden="true">{arrow}</span> <span class="sr-only">{sr_direction} </span>{delta} vs last mock</div>'
    else:
        # Invisible spacer so all 4 KPI cards align at the exact same vertical baseline
        delta_elem = '<div class="metric-delta metric-delta-spacer" aria-hidden="true">&nbsp;</div>'

    sub_elem = (
        f'<div class="metric-subtitle">{subtitle}</div>'
        if subtitle
        else '<div class="metric-subtitle metric-delta-spacer" aria-hidden="true">&nbsp;</div>'
    )

    clean_label = html.escape(sanitize_text(label))
    clean_val = html.escape(str(value))

    card_html = textwrap.dedent(f"""\
<div class="metric-box" role="region" aria-label="{clean_label} metric">
<div class="metric-header">
<span class="metric-label">{clean_label}</span>
<span class="metric-icon" aria-hidden="true">{icon}</span>
</div>
<div class="metric-value">{clean_val}</div>
<div class="metric-footer">
{delta_elem}
{sub_elem}
</div>
</div>""").strip()

    st.markdown(card_html, unsafe_allow_html=True)

def render_feature_card(title: str, description: str, icon: str, tag: Optional[str] = None):
    """Renders a feature card for the landing page or module showcase."""
    tag_html = f'<span class="badge badge-beginner" style="margin-left: auto;">{html.escape(tag)}</span>' if tag else ""
    card_html = textwrap.dedent(f"""\
<div class="feature-card">
<div style="display: flex; align-items: center; justify-content: space-between;">
<div class="feature-icon-wrapper">{icon}</div>
{tag_html}
</div>
<div class="feature-title">{html.escape(title)}</div>
<div class="feature-description">{html.escape(description)}</div>
</div>""").strip()

    st.markdown(card_html, unsafe_allow_html=True)

def render_interview_question_card(
    question_text: str,
    category: str,
    question_number: int,
    total_questions: int,
    is_follow_up: bool = False,
    is_offline: bool = False,
    interviewer_intent: str = ""
):
    """
    Renders the live interview question card.
    Guarantees:
    - Zero raw HTML leaks: completely strips any nested tags and escapes text safely
    - Full mobile and desktop responsiveness without horizontal scrollbars
    - Distinct engine badge: Live AI Mode vs Offline Question Bank
    - Preserves category and interviewer focus sections cleanly
    """
    clean_q = sanitize_text(question_text)
    clean_cat = sanitize_text(category) or "Technical"
    clean_intent = sanitize_text(interviewer_intent)

    fu_badge = '<span class="badge-followup"><span aria-hidden="true">⚡</span> Follow-up Question</span>' if is_follow_up else ''
    
    if not is_offline:
        engine_badge = '<span class="engine-badge engine-live"><span aria-hidden="true">🟢</span> Live AI: Gemini 2.5 Flash</span>'
    else:
        engine_badge = '<span class="engine-badge engine-offline"><span aria-hidden="true">📌</span> Offline Question Bank</span>'

    intent_html = ""
    if clean_intent:
        intent_html = f'<div class="interview-focus-box"><span aria-hidden="true">🎯</span> <b>Interviewer Focus:</b> {html.escape(clean_intent)}</div>'

    card_html = textwrap.dedent(f"""\
<div class="interview-question-card" role="region" aria-label="Interview Question Card: Question {question_number} of {total_questions}">
<div class="interview-question-header">
<div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
<span class="badge-cat">{html.escape(clean_cat)}</span>
{fu_badge}
</div>
<div>
{engine_badge}
</div>
</div>
<h3 class="interview-question-title">{html.escape(clean_q)}</h3>
{intent_html}
</div>""").strip()

    st.markdown(card_html, unsafe_allow_html=True)

def render_evaluation_summary_card(
    scores_100: Dict[str, float],
    scores_10: Dict[str, float],
    is_offline: bool = False,
    eval_engine: str = ""
):
    """
    Renders the score summary header for an evaluated interview question.
    Clearly and transparently displays whether evaluation was done by Live AI or Offline Heuristic Engine.
    """
    ovr = scores_100.get("overall", 0.0)
    ovr_color = "#10B981" if ovr >= 75 else ("#F59E0B" if ovr >= 60 else "#EF4444")

    acc_10 = scores_10.get("accuracy", round(scores_100.get("accuracy", 0) / 10, 1))
    conc_10 = scores_10.get("conceptual", round(scores_100.get("conceptual", 0) / 10, 1))
    comm_10 = scores_10.get("communication", round(scores_100.get("clarity", 0) / 10, 1))
    rel_10 = scores_10.get("relevance", round(scores_100.get("relevance", 0) / 10, 1))

    if not is_offline:
        mode_box = textwrap.dedent("""\
<div class="eval-mode-box eval-mode-live">
<span aria-hidden="true">⚡</span> <b>Evaluation Engine:</b> Live AI Evaluation powered by <b>Google Gemini 2.5 Flash</b>.
</div>""")
    else:
        mode_box = textwrap.dedent("""\
<div class="eval-mode-box eval-mode-offline">
<span aria-hidden="true">📌</span> <b>Evaluation Engine:</b> <b>Offline Heuristic Audit Engine</b> (Rule-based evaluation — Gemini API key is not active in this session).
</div>""")

    card_html = textwrap.dedent(f"""\
<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 14px; padding: 1.25rem 1.5rem; margin-bottom: 1.25rem; width: 100%; box-sizing: border-box; overflow-x: hidden;" role="region" aria-label="Question Evaluation Summary">
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
<div>
<div style="font-size: 0.75rem; font-weight: 700; color: #334155; text-transform: uppercase; letter-spacing: 0.05em;">Question Score</div>
<div style="font-size: 1.65rem; font-weight: 800; color: {ovr_color}; line-height: 1.2;" aria-label="Score: {ovr:.1f} percent">{ovr:.1f}%</div>
</div>
<div style="display: flex; gap: 16px; font-size: 0.85rem; color: #334155; flex-wrap: wrap;">
<div><b>Accuracy:</b> {acc_10}/10</div>
<div><b>Conceptual:</b> {conc_10}/10</div>
<div><b>Communication:</b> {comm_10}/10</div>
<div><b>Relevance:</b> {rel_10}/10</div>
</div>
</div>
{mode_box}
</div>""").strip()

    st.markdown(card_html, unsafe_allow_html=True)

def render_honest_feedback_comparison(
    question: str,
    user_answer: str,
    honest_critique: str,
    incorrect_concepts: List[str],
    missing_info: List[str],
    improved_answer: str,
    why_better: str
):
    """
    Renders the side-by-side Answer Improvement & Honest Feedback comparison.
    Satisfies Module 2 & 3 core requirements with clean dedented HTML, safe escaping,
    and responsive wrapping without horizontal scrollbars.
    """
    clean_q = sanitize_text(question)
    clean_ans = sanitize_text(user_answer)
    clean_crit = sanitize_text(honest_critique)
    clean_imp = sanitize_text(improved_answer)
    clean_why = sanitize_text(why_better)

    if incorrect_concepts:
        incorrect_items = "".join([f"<li style='margin-bottom: 6px;'><b>{html.escape(sanitize_text(c))}</b></li>" for c in incorrect_concepts])
    else:
        incorrect_items = "<li>No factual misconceptions detected.</li>"

    if missing_info:
        missing_items = "".join([f"<li style='margin-bottom: 6px;'>{html.escape(sanitize_text(m))}</li>" for m in missing_info])
    else:
        missing_items = "<li>No critical components omitted.</li>"

    card_html = textwrap.dedent(f"""\
<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 1.5rem; margin-top: 0.75rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); width: 100%; box-sizing: border-box; overflow-x: hidden; word-break: break-word;" role="region" aria-label="Feedback and Benchmark Analysis">
<div style="font-size: 0.75rem; font-weight: 700; color: #3730A3; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.35rem;">
Question Asked
</div>
<h4 style="font-size: 1.1rem; font-weight: 600; color: #0F172A; margin: 0 0 1.25rem 0; line-height: 1.45; word-break: break-word;">
"{html.escape(clean_q)}"
</h4>

<div style="display: grid; grid-template-columns: 1fr; gap: 1rem; margin-bottom: 0.5rem; width: 100%; box-sizing: border-box;">
<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.15rem; box-sizing: border-box;">
<h5 style="margin: 0 0 0.4rem 0; font-weight: 700; color: #334155; font-size: 0.88rem;">
Candidate's Original Answer
</h5>
<div style="font-style: italic; color: #334155; line-height: 1.55; font-size: 0.93rem; word-break: break-word;">
"{html.escape(clean_ans)}"
</div>
</div>

<div class="feedback-card feedback-critical">
<h5 style="margin: 0 0 0.5rem 0; font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; gap: 8px;">
<span aria-hidden="true">⚠️</span> Honest Feedback Engine Critique
</h5>
<div style="font-size: 0.925rem; line-height: 1.55; margin-bottom: 0.75rem; word-break: break-word;">
{html.escape(clean_crit)}
</div>

<div style="margin-top: 0.75rem; border-top: 1px solid #FECACA; padding-top: 0.75rem;">
<div style="font-weight: 700; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.35rem;">
<span aria-hidden="true">❌</span> Incorrect Technical Concepts
</div>
<ul style="margin: 0; padding-left: 1.25rem; font-size: 0.875rem; line-height: 1.5;">
{incorrect_items}
</ul>
</div>

<div style="margin-top: 0.75rem; border-top: 1px solid #FECACA; padding-top: 0.75rem;">
<div style="font-weight: 700; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.35rem;">
<span aria-hidden="true">🔍</span> Missing Information &amp; Trade-offs
</div>
<ul style="margin: 0; padding-left: 1.25rem; font-size: 0.875rem; line-height: 1.5;">
{missing_items}
</ul>
</div>
</div>

<div class="feedback-card feedback-improvement">
<h5 style="margin: 0 0 0.5rem 0; font-weight: 700; font-size: 0.95rem; display: flex; align-items: center; gap: 8px;">
<span aria-hidden="true">✨</span> Improved Benchmark Sample Answer
</h5>
<div style="font-size: 0.95rem; line-height: 1.6; margin-bottom: 0.75rem; color: #064E3B; word-break: break-word;">
{html.escape(clean_imp)}
</div>

<div style="margin-top: 0.75rem; border-top: 1px solid #A7F3D0; padding-top: 0.75rem;">
<div style="font-weight: 700; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.35rem; color: #065F46;">
<span aria-hidden="true">💡</span> Why This Answer Scores Higher
</div>
<div style="font-size: 0.875rem; line-height: 1.55; color: #064E3B; word-break: break-word;">
{html.escape(clean_why)}
</div>
</div>
</div>
</div>
</div>""").strip()

    st.markdown(card_html, unsafe_allow_html=True)
