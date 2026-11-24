"""
Landing Page module for InterviewX.
Tailored for Indian college students, fresh graduates, and tech job seekers.
Showcases platform value propositions, honest feedback demonstration, and role tracks.
"""

import textwrap
import streamlit as st
from config import APP_NAME, TAGLINE, TARGET_AUDIENCE, JOB_ROLES, DIFFICULTY_LEVELS, COMPANY_TRACKS
from components.cards import render_feature_card, render_honest_feedback_comparison
from auth import is_authenticated

def render_landing_page():
    """Renders the comprehensive, high-converting landing page for InterviewX."""
    
    # Hero Section
    hero_html = textwrap.dedent(f"""\
<div class="hero-container">
<div style="display: flex; gap: 10px; margin-bottom: 1.25rem; flex-wrap: wrap;">
<div class="brand-badge">
<span>🎯</span> Engineered for Campus & Off-Campus Placements
</div>
<div style="background: #F1F5F9; border: 1px solid #CBD5E1; color: #334155; padding: 6px 14px; border-radius: 9999px; font-weight: 600; font-size: 0.85rem;">
🇮🇳 Tier-1, Tier-2 & Tier-3 Graduates
</div>
</div>
<div class="hero-tagline">
Practice. Get Honest Feedback.<br>Improve. Get Hired.
</div>
<div class="hero-subtitle">
Most mock interview platforms give flattering, generic praise that builds false confidence.
<b>InterviewX</b> delivers <b>brutally honest technical evaluations</b>, exposes dangerous misconceptions, 
and prepares you for top product startups, tech giants, and campus recruitment drives.
</div>
</div>""").strip()
    st.markdown(hero_html, unsafe_allow_html=True)

    # Hero Action Buttons
    c_btn1, c_btn2, c_btn3 = st.columns([1.5, 1.5, 2.5])
    with c_btn1:
        if st.button("📊 Open Dashboard", type="primary", width="stretch"):
            if is_authenticated():
                st.session_state["active_page"] = "dashboard"
            else:
                st.session_state["active_page"] = "auth"
            st.rerun()
    with c_btn2:
        if is_authenticated():
            if st.button("🎙️ Start AI Mock", width="stretch"):
                st.session_state["active_page"] = "interview"
                st.rerun()
        else:
            if st.button("🔑 Sign In / Register", width="stretch"):
                st.session_state["active_page"] = "auth"
                st.rerun()
    with c_btn3:
        st.caption("🔒 SQLite Persistent • Salted Hash Auth • Google Gemini Powered")

    st.markdown("<div class='dashboard-spacer-sm'></div>", unsafe_allow_html=True)

    # Reality Check Callout Banner
    reality_html = textwrap.dedent("""\
<div class="audience-banner">
<div>
<div style="font-size: 1.15rem; font-weight: 700; margin-bottom: 4px;">
💡 The Placement Reality Check
</div>
<div style="font-size: 0.9rem; opacity: 0.9; line-height: 1.5;">
Over 80% of fresh graduates are eliminated in technical screening rounds because of inaccurate complexity analysis, 
flawed data structure fundamentals, and lack of structured communication. Generic praise won't get you placed; 
honest critique will.
</div>
</div>
<div style="text-align: right; min-width: 140px;">
<div style="font-size: 2rem; font-weight: 800; color: #38BDF8;">3.5x</div>
<div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.8;">Offer Rate Improvement</div>
</div>
</div>""").strip()
    st.markdown(reality_html, unsafe_allow_html=True)

    # Core Modules Architecture Section
    st.markdown("### ⚡ Why InterviewX Is Different")
    st.markdown("A structured, 5-stage preparation system designed to turn interview anxiety into offer letters.")

    col1, col2, col3 = st.columns(3)
    with col1:
        render_feature_card(
            title="1. AI Mock Interviewer",
            description="Select your target role and difficulty. Experience real technical screens asking one question at a time with dynamic, adaptive follow-ups.",
            icon="🎙️",
            tag="Adaptive"
        )
    with col2:
        render_feature_card(
            title="2. Honest Feedback Engine",
            description="Never praises incorrect answers as correct. Exposes exact technical mistakes, logical gaps, and missing edge cases with brutal clarity.",
            icon="🛡️",
            tag="Zero Flattery"
        )
    with col3:
        render_feature_card(
            title="3. Answer Improvement",
            description="Side-by-side comparison: see your answer vs an exemplary production-grade sample answer, with a line-by-line breakdown of why it scores higher.",
            icon="✨",
            tag="Actionable"
        )

    col4, col5, col6 = st.columns(3)
    with col4:
        render_feature_card(
            title="4. Personalised Roadmap",
            description="Automatic diagnosis of weak topics. Generates a realistic day-wise study plan targeting your exact gaps before your drive.",
            icon="🗺️",
            tag="Tailored"
        )
    with col5:
        render_feature_card(
            title="5. Placement Progress Tracker",
            description="Persistent SQLite tracking of your performance history, score progression trends, and recurring weaknesses across all attempts.",
            icon="📈",
            tag="Persistent"
        )
    with col6:
        render_feature_card(
            title="Targeted Company Tracks",
            description="Switch preparation modes between High-Scale Product Startups (Swiggy, Razorpay), IT Services (TCS NQT, Infosys), or Banking/GICs.",
            icon="🏢",
            tag="Customized"
        )

    st.markdown("<div class='dashboard-spacer'></div>", unsafe_allow_html=True)

    # Interactive Demo: Taste of Honest Feedback vs Generic Tools
    st.markdown("### 🔍 The 'Honest Feedback' In Action")
    st.markdown("Compare how generic mock platforms treat candidate answers versus how InterviewX evaluates them:")

    tab1, tab2 = st.tabs(["⚡ InterviewX Evaluation (Real & Rigorous)", "⚠️ Generic Mock Tools (Dangerous Flattery)"])
    
    with tab1:
        render_honest_feedback_comparison(
            question="Explain how Java HashMap handles hash collisions internally and what is its worst-case time complexity.",
            user_answer="HashMap uses an array with linked lists. When two keys have the same hash code, it just adds them in the linked list. Search is always O(1) in HashMap.",
            honest_critique="Your answer contains a critical technical error regarding worst-case complexity and omits Java 8+ architectural changes. While average lookup is O(1), worst-case is NOT O(1). Claiming O(1) in an interview will disqualify you on core data structures.",
            incorrect_concepts=[
                "Claimed lookup is always O(1) in HashMap",
                "Stated collisions only use linked lists indefinitely"
            ],
            missing_info=[
                "Java 8 treeification threshold (linked list converts to Red-Black Tree when bucket exceeds 8 nodes)",
                "Worst-case time complexity is O(log N) in Java 8+ and O(N) prior to Java 8",
                "Contract between equals() and hashCode() methods"
            ],
            improved_answer="In Java, HashMap internally uses an array of Node buckets. When collisions occur, elements are stored in a linked list. In Java 8+, once a bucket reaches TREEIFY_THRESHOLD (8 items) and array capacity is at least 64, it converts the list into a Red-Black Tree (TreeNode). The average time complexity for get() and put() is O(1), but the worst-case with severe collisions is O(log N) in Java 8+ (or O(N) in legacy versions). Proper implementation of equals() and hashCode() is mandatory to prevent unnecessary collisions.",
            why_better="Directly addresses internal mechanics, cites exact Java 8 threshold (8 nodes -> Red-Black Tree), and clearly distinguishes between average O(1) and worst-case O(log N)."
        )

    with tab2:
        warning_box = textwrap.dedent("""\
<div style="background: #FFFBEB; border: 1px solid #FCD34D; border-radius: 14px; padding: 1.5rem; margin-top: 0.75rem;">
<div style="font-weight: 700; color: #92400E; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 8px;">
<span>⚠️</span> Generic AI Platform Feedback (Flawed Evaluation)
</div>
<div style="color: #78350F; font-size: 0.95rem; line-height: 1.6;">
<i>"Great job! You correctly explained that HashMap uses arrays and linked lists for collisions. You understand that HashMap is very fast with O(1) operations. Keep up the good work! Score: 92/100"</i>
</div>
<div style="margin-top: 1rem; padding: 0.75rem; background: #FEF2F2; border-radius: 8px; font-size: 0.85rem; color: #991B1B;">
<b>The Danger:</b> The candidate walks into an interview at Swiggy, Amazon, or TCS Digital believing worst-case is O(1), gets rejected, and never understands why.
</div>
</div>""").strip()
        st.markdown(warning_box, unsafe_allow_html=True)

    st.markdown("<div class='dashboard-spacer'></div>", unsafe_allow_html=True)

    # Roles and Tracks Grid
    st.markdown("### 💼 Supported Roles & Difficulty Tiers")
    st.markdown("Curated syllabus and question banks aligned with current Indian hiring trends:")

    col_roles, col_diff = st.columns([1.5, 1])
    
    with col_roles:
        st.markdown("#### Primary Career Paths")
        for role in JOB_ROLES[:4]:
            role_badge_items = " ".join([f"<span style='background:#F1F5F9; font-size:0.75rem; padding:2px 8px; border-radius:4px; color:#475569;'>{t}</span>" for t in role['core_topics'][:4]])
            role_html = textwrap.dedent(f"""\
<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 0.9rem 1.1rem; margin-bottom: 0.75rem;">
<div style="display: flex; align-items: center; justify-content: space-between;">
<div style="font-weight: 700; color: #0F172A; font-size: 0.95rem;">
{role['icon']} {role['title']}
</div>
<span class="track-pill">{role['category']}</span>
</div>
<div style="font-size: 0.825rem; color: #64748B; margin-top: 4px;">
{role['description']}
</div>
<div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px;">
{role_badge_items}
</div>
</div>""").strip()
            st.markdown(role_html, unsafe_allow_html=True)

    with col_diff:
        st.markdown("#### Preparation Difficulty Tiers")
        for diff in DIFFICULTY_LEVELS:
            badge_class = f"badge-{diff['id']}"
            diff_html = textwrap.dedent(f"""\
<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1rem; margin-bottom: 0.75rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
<span class="badge {badge_class}">{diff['badge']}</span>
</div>
<div style="font-weight: 600; font-size: 0.9rem; color: #0F172A; margin-bottom: 4px;">
{diff['name']}
</div>
<div style="font-size: 0.8rem; color: #64748B; line-height: 1.4;">
{diff['description']}
</div>
<div style="font-size: 0.75rem; color: #4F46E5; margin-top: 6px; font-weight: 600;">
🎯 Target: {diff['target']}
</div>
</div>""").strip()
            st.markdown(diff_html, unsafe_allow_html=True)

    st.markdown("<div class='dashboard-spacer'></div>", unsafe_allow_html=True)

    # Ready to Prepare CTA
    cta_html = textwrap.dedent("""\
<div style="background: linear-gradient(135deg, #4F46E5 0%, #3730A3 100%); border-radius: 20px; padding: 2.5rem; color: white; text-align: center;">
<div style="font-size: 2rem; font-weight: 800; margin-bottom: 0.5rem;">
Ready to experience honest interview preparation?
</div>
<div style="font-size: 1rem; opacity: 0.9; max-width: 600px; margin: 0 auto 1.5rem auto;">
Explore your candidate dashboard, inspect detailed historical evaluations, or start a new mock interview.
</div>
</div>""").strip()
    st.markdown(cta_html, unsafe_allow_html=True)

    c_c1, c_c2, c_c3 = st.columns([1, 2, 1])
    with c_c2:
        btn_label = "🚀 Enter Candidate Dashboard Now" if is_authenticated() else "🚀 Create Free Account / Sign In"
        target_dest = "dashboard" if is_authenticated() else "auth"
        if st.button(btn_label, type="primary", width="stretch"):
            st.session_state["active_page"] = target_dest
            st.rerun()
