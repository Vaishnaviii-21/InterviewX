"""
AI Mock Interviewer module for InterviewX.
Full multi-turn realistic interview session engine:
- Supports 12 Job Roles, 6 Interview Categories, 3 Difficulty Tiers
- Configurable durations (5, 10, 15, 30 minutes) and question counts
- One-question-at-a-time execution with adaptive follow-ups
- Live answer evaluation scored across 4 core criteria (out of 10)
- Full persistence to SQLite with automatic weakness and strength tracking
"""

import time
import json
import streamlit as st
from auth import get_current_user, is_authenticated
from config import (
    JOB_ROLES,
    DIFFICULTY_LEVELS,
    COMPANY_TRACKS,
    INTERVIEW_CATEGORIES,
    INTERVIEW_DURATIONS,
    is_api_key_configured
)
from database import (
    get_candidate_resume,
    create_interview_session,
    record_question_and_feedback,
    finalize_interview_session,
    record_topic_status
)
from services.gemini_service import GeminiService
from components.cards import (
    render_honest_feedback_comparison,
    render_interview_question_card,
    render_evaluation_summary_card,
    sanitize_text
)

def render_interview_page():
    """Main entry point for AI Mock Interviewer."""
    logged_in = is_authenticated()
    curr_user = get_current_user()
    user_id = curr_user["id"] if (logged_in and curr_user) else 1

    # Check if an active interview session is running in session_state
    if "active_interview" in st.session_state and st.session_state["active_interview"].get("in_progress"):
        _render_active_interview(user_id)
    else:
        _render_interview_configuration(user_id)

def _render_interview_configuration(user_id: int):
    """Renders the comprehensive interview configuration screen."""
    st.markdown("## 🎙️ AI Mock Interviewer")
    st.markdown(
        "Experience realistic technical and HR interview rounds. The AI interviewer asks "
        "**one question at a time**, dynamically explores your technical depth, and provides "
        "uncompromising, constructive feedback."
    )

    if is_api_key_configured():
        st.success(
            "⚡ **Live AI Mode Active:** Connected to Google Gemini 2.5 Flash. "
            "Questions and evaluations will be generated dynamically in real-time by the AI.",
            icon="✅"
        )
    else:
        st.info(
            "📌 **Offline Audit Mode Active:** Gemini API key is not detected in environment. "
            "InterviewX is operating in offline mode using our curated technical question banks and heuristic evaluation engine. "
            "To enable live AI generation, configure your `GEMINI_API_KEY` in `.env` or in the sidebar under 'Gemini API Settings'.",
            icon="ℹ️"
        )

    # Check for active resume
    resume_data = get_candidate_resume(user_id)
    has_resume = bool(resume_data and resume_data.get("parsed_skills"))

    with st.container(border=True):
        st.markdown("#### 🎯 Configure Your Mock Interview Session")
        st.caption("Customize the interview role, category, target track, and length.")

        col1, col2 = st.columns(2)

        with col1:
            # 1. Job Role
            role_options = [f"{r['icon']} {r['title']}" for r in JOB_ROLES]
            role_idx = st.selectbox("1. Target Job Role:", range(len(role_options)), format_func=lambda i: role_options[i])
            selected_role = JOB_ROLES[role_idx]

            # 2. Category
            cat_options = [f"{c['icon']} {c['name']}" for c in INTERVIEW_CATEGORIES]
            cat_default = 4 if st.session_state.get("use_resume_mode") and has_resume else 0
            cat_idx = st.selectbox("3. Interview Category:", range(len(cat_options)), index=cat_default, format_func=lambda i: cat_options[i])
            selected_cat = INTERVIEW_CATEGORIES[cat_idx]

            # 3. Target Track
            track_options = [f"{t['icon']} {t['name']}" for t in COMPANY_TRACKS]
            track_idx = st.selectbox("5. Target Company Track:", range(len(track_options)), format_func=lambda i: track_options[i])
            selected_track = COMPANY_TRACKS[track_idx]

        with col2:
            # 4. Difficulty Tier
            diff_options = [f"{d['badge']} - {d['name'].split('(')[1].replace(')', '')}" for d in DIFFICULTY_LEVELS]
            diff_idx = st.selectbox("2. Difficulty Level:", range(len(diff_options)), index=1, format_func=lambda i: diff_options[i])
            selected_diff = DIFFICULTY_LEVELS[diff_idx]

            # 5. Duration & Question Count
            dur_options = [d["label"] for d in INTERVIEW_DURATIONS]
            dur_idx = st.selectbox("4. Interview Duration & Scope:", range(len(dur_options)), index=1, format_func=lambda i: dur_options[i])
            selected_dur = INTERVIEW_DURATIONS[dur_idx]

            # 6. Resume Integration
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            if has_resume:
                use_resume = st.checkbox(
                    f"📄 Tailor questions using my resume ({resume_data.get('file_name', 'Resume')})",
                    value=True if (st.session_state.get("use_resume_mode") or selected_cat["id"] == "resume") else False,
                    help="AI will generate questions directly probing your claimed projects and skills."
                )
            else:
                st.caption("ℹ️ *No resume uploaded. [Upload a resume in Resume Analyzer](#) to enable resume-based questions.*")
                use_resume = False

    # Launch Button
    col_btn1, col_btn2 = st.columns([1.5, 3])
    with col_btn1:
        if st.button("🚀 Start Interview", type="primary", width="stretch"):
            # Map duration to questions
            dur_mins = selected_dur["minutes"]
            q_target = 3 if dur_mins == 5 else (5 if dur_mins == 10 else (8 if dur_mins == 15 else 10))

            # Create session in SQLite
            session_id = create_interview_session(
                user_id=user_id,
                role_id=selected_role["id"],
                role_title=selected_role["title"],
                difficulty=selected_diff["name"],
                interview_type=selected_cat["name"],
                target_company_track=selected_track["name"],
                resume_id=resume_data.get("id") if (has_resume and use_resume) else None,
                duration_minutes=dur_mins
            )

            # Initialize active interview in session state
            st.session_state["active_interview"] = {
                "in_progress": True,
                "session_id": session_id,
                "role_title": selected_role["title"],
                "difficulty": selected_diff["name"],
                "interview_type": selected_cat["name"],
                "target_company_track": selected_track["name"],
                "duration_minutes": dur_mins,
                "total_target_questions": q_target,
                "current_question_number": 1,
                "questions_history": [],
                "current_question": None,
                "evaluation_shown": False,
                "last_evaluation": None,
                "start_time": time.time(),
                "use_resume": use_resume,
                "resume_data": resume_data if (has_resume and use_resume) else None
            }
            # Reset resume mode flag
            st.session_state["use_resume_mode"] = False
            st.rerun()

    with col_btn2:
        st.caption(f"Ready: **{selected_role['title']}** • **{selected_cat['name']}** • **{selected_diff['badge']} Tier**")

def _render_active_interview(user_id: int):
    """Renders the live multi-turn mock interview interface."""
    state = st.session_state["active_interview"]
    session_id = state["session_id"]
    current_q_num = state["current_question_number"]
    total_q = state["total_target_questions"]
    role_title = state["role_title"]
    difficulty = state["difficulty"]
    interview_type = state["interview_type"]
    track = state["target_company_track"]
    resume_data = state.get("resume_data")

    # 1. Generate or fetch current question
    if state["current_question"] is None:
        with st.spinner("🤖 Interviewer is preparing your question..."):
            svc = GeminiService()
            q_data = svc.generate_interview_question(
                role_title=role_title,
                difficulty=difficulty,
                interview_type=interview_type,
                question_number=current_q_num,
                target_company_track=track,
                previous_context=state["questions_history"],
                resume_context=resume_data
            )
            state["current_question"] = q_data

    curr_q = state["current_question"]

    # 2. Top Header & Progress Bar
    progress_val = min(1.0, (current_q_num - 1) / max(1, total_q))
    st.progress(progress_val)

    col_h1, col_h2, col_h3 = st.columns([2, 1, 1], vertical_alignment="center")
    with col_h1:
        st.markdown(f"**{role_title}** • <span style='color: #4F46E5; font-weight: 700;'>Question {current_q_num} of {total_q}</span>", unsafe_allow_html=True)
    with col_h2:
        st.caption(f"Tier: {difficulty.split('(')[0].strip()}")
    with col_h3:
        if st.button("🛑 End Interview Early", help="Finishes and saves evaluation of answered questions"):
            _finish_interview(state, user_id)
            return

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 3. Question Display Card (Using dedicated, sanitized, responsive renderer)
    cat_badge = curr_q.get("category", "Technical")
    is_fu = curr_q.get("is_follow_up", False)
    is_offline = curr_q.get("is_offline", not is_api_key_configured())

    render_interview_question_card(
        question_text=curr_q.get("question_text", "Question"),
        category=cat_badge,
        question_number=current_q_num,
        total_questions=total_q,
        is_follow_up=is_fu,
        is_offline=is_offline,
        interviewer_intent=curr_q.get("interviewer_intent", "")
    )

    # 4. Answer Input / Evaluation State
    if not state.get("evaluation_shown"):
        # Answer entry form
        user_answer = st.text_area(
            "Your Answer:",
            placeholder="Type your structured answer here. Be specific, explain underlying mechanics, state complexities, and discuss trade-offs...",
            height=160,
            key=f"ans_input_{current_q_num}"
        )

        col_sub1, col_sub2 = st.columns([1.5, 3])
        with col_sub1:
            if st.button("⚡ Submit Answer for Evaluation", type="primary", width="stretch"):
                if not user_answer or len(user_answer.strip()) < 5:
                    st.warning("Please provide a substantive answer before submitting.")
                else:
                    with st.spinner("Analyzing answer with Honest Feedback Engine..."):
                        svc = GeminiService()
                        eval_res = svc.evaluate_answer_honest(
                            question_text=curr_q.get("question_text", ""),
                            user_answer=user_answer,
                            role_title=role_title,
                            difficulty=difficulty
                        )

                        # Store in SQLite immediately
                        scores = eval_res.get("scores", {})
                        record_question_and_feedback(
                            session_id=session_id,
                            question_number=current_q_num,
                            question_text=curr_q.get("question_text", ""),
                            category=cat_badge,
                            user_answer=user_answer,
                            scores=scores,
                            honest_feedback=eval_res.get("honest_critique", ""),
                            incorrect_concepts=json.dumps(eval_res.get("incorrect_concepts", [])),
                            missing_information=json.dumps(eval_res.get("missing_information", [])),
                            improved_answer=eval_res.get("improved_sample_answer", ""),
                            improvement_reason=eval_res.get("why_improved_is_better", ""),
                            is_resume_based=state.get("use_resume", False)
                        )

                        # Update weaknesses / strengths in database
                        for t in eval_res.get("detected_topics", []):
                            record_topic_status(
                                user_id=user_id,
                                topic_name=t.get("topic", "Topic"),
                                category=t.get("category", "Technical"),
                                status=t.get("status", "weakness"),
                                notes=eval_res.get("honest_critique", "")[:120]
                            )

                        # Update state
                        state["evaluation_shown"] = True
                        state["last_evaluation"] = {
                            "question": curr_q.get("question_text", ""),
                            "user_answer": user_answer,
                            "eval": eval_res
                        }
                        state["questions_history"].append({
                            "question_text": curr_q.get("question_text", ""),
                            "user_answer": user_answer,
                            "overall_score": scores.get("overall", 50.0)
                        })
                        st.rerun()

        with col_sub2:
            st.caption("🎙️ *Tip: You can use voice dictation (Win + H on Windows) to speak your answer naturally.*")

    else:
        # Display Honest Feedback Comparison for this question
        last = state["last_evaluation"]
        e = last["eval"]
        sc_10 = e.get("scores_10", {})
        sc_100 = e.get("scores", {})
        eval_is_offline = e.get("is_offline", not is_api_key_configured())

        render_evaluation_summary_card(
            scores_100=sc_100,
            scores_10=sc_10,
            is_offline=eval_is_offline,
            eval_engine=e.get("evaluation_engine", "")
        )

        render_honest_feedback_comparison(
            question=last["question"],
            user_answer=last["user_answer"],
            honest_critique=e.get("honest_critique", ""),
            incorrect_concepts=e.get("incorrect_concepts", []),
            missing_info=e.get("missing_information", []),
            improved_answer=e.get("improved_sample_answer", ""),
            why_better=e.get("why_improved_is_better", "")
        )

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

        # Progression Controls
        if current_q_num < total_q:
            if st.button(f"➡️ Proceed to Question {current_q_num + 1}", type="primary", width="stretch"):
                state["current_question_number"] += 1
                state["current_question"] = None
                state["evaluation_shown"] = False
                state["last_evaluation"] = None
                st.rerun()
        else:
            if st.button("🎉 Complete Interview & View Performance Report", type="primary", width="stretch"):
                _finish_interview(state, user_id)

def _finish_interview(state: dict, user_id: int):
    """Finalizes session aggregates, marks status completed, and navigates to Feedback report."""
    session_id = state["session_id"]
    from database.models import get_interview_questions

    # Fetch actual recorded questions to compute precise session aggregates
    questions = get_interview_questions(session_id)
    if questions:
        count = len(questions)
        avg_ovr = sum(q.get("overall_score", 0.0) for q in questions) / count
        avg_acc = sum(q.get("accuracy_score", 0.0) for q in questions) / count
        avg_rel = sum(q.get("relevance_score", 0.0) for q in questions) / count
        avg_comp = sum(q.get("completeness_score", 0.0) for q in questions) / count
        avg_clar = sum(q.get("clarity_score", 0.0) for q in questions) / count
        avg_conc = sum(q.get("conceptual_score", 0.0) for q in questions) / count

        summary_desc = (
            f"Candidate completed {count} question(s) for {state['role_title']} ({state['difficulty']}). "
            f"Demonstrated average accuracy of {avg_acc:.1f}% and clarity of {avg_clar:.1f}%."
        )

        readiness = "Placement Ready" if avg_ovr >= 75 else ("Needs Target Polish" if avg_ovr >= 60 else "Early Prep Phase")

        finalize_interview_session(
            session_id=session_id,
            summary=summary_desc,
            overall_score=round(avg_ovr, 1),
            accuracy_score=round(avg_acc, 1),
            relevance_score=round(avg_rel, 1),
            completeness_score=round(avg_comp, 1),
            clarity_score=round(avg_clar, 1),
            conceptual_score=round(avg_conc, 1),
            readiness_assessment=readiness
        )

    # Clear active interview state
    del st.session_state["active_interview"]
    st.session_state["view_session_id"] = session_id
    st.session_state["active_page"] = "feedback"
    st.success("Interview completed! Generating comprehensive feedback report...")
    st.rerun()
