"""
Module: Resume Analyzer for InterviewX.
Allows candidates to upload resumes (PDF, DOCX, TXT), extracts text without external dependencies,
identifies technical skills, educational background, projects, strengths, missing skills,
and generates tailored interview questions with the option to launch a resume-based interview.
"""

import streamlit as st
from auth import get_current_user, is_authenticated
from database import (
    save_candidate_resume,
    get_candidate_resume,
    delete_candidate_resume
)
from utils.resume_parser import ResumeParser, ResumeAnalyzer

def render_resume_analyzer_page():
    """Renders the Resume Analyzer interface with upload, analysis, and insights."""
    st.markdown('<h1 class="page-title-h1"><span aria-hidden="true">📄</span> Resume Analyzer &amp; Career Profiler</h1>', unsafe_allow_html=True)
    st.markdown(
        "Upload your resume to extract skills, detect missing competencies, get actionable improvement tips, "
        "and generate **custom interview questions based directly on your projects and stack**."
    )

    logged_in = is_authenticated()
    curr_user = get_current_user()
    user_id = curr_user["id"] if (logged_in and curr_user) else 1

    # Fetch existing active resume if already uploaded
    existing_resume = get_candidate_resume(user_id)

    # 1. File Upload Section
    with st.container():
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);">
            <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A; margin-bottom: 0.35rem;">
                📤 Upload Your Resume
            </div>
            <div style="font-size: 0.85rem; color: #64748B; margin-bottom: 1rem;">
                Supported file formats: <b>PDF</b>, <b>DOCX</b> (Word), and <b>TXT</b> (Max size: 10MB).
            </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Upload resume file:",
            type=["pdf", "docx", "txt", "md"],
            label_visibility="collapsed"
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # Process new upload
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name

        with st.spinner("Extracting text and analyzing competencies with AI engine..."):
            extracted_text = ResumeParser.extract_text_from_bytes(file_bytes, file_name)
            if not extracted_text or len(extracted_text.strip()) < 30:
                st.error("Could not extract readable text from this file. Please verify it is a valid PDF or DOCX file.")
            else:
                analysis = ResumeAnalyzer.analyze_resume(extracted_text, file_name)
                
                # Save to persistent database
                save_candidate_resume(
                    user_id=user_id,
                    file_name=file_name,
                    raw_text=extracted_text,
                    parsed_skills=analysis.get("parsed_skills", []),
                    parsed_projects=analysis.get("parsed_projects", []),
                    parsed_experience=analysis.get("parsed_experience", []),
                    parsed_education=analysis.get("parsed_education", []),
                    strengths=analysis.get("strengths", []),
                    missing_skills=analysis.get("missing_skills", []),
                    suggested_improvements=analysis.get("suggested_improvements", []),
                    interview_questions=analysis.get("interview_questions", []),
                    summary=analysis.get("summary", "")
                )
                st.success(f"Successfully parsed and analyzed resume: **{file_name}**!")
                # Refresh local reference
                existing_resume = get_candidate_resume(user_id)

    # 2. Display Parsed Resume Insights
    if not existing_resume:
        st.info(
            "💡 **No resume uploaded yet:** Upload your resume above to unlock tailored mock interview questions, "
            "missing skill detection, and targeted placement preparation.",
            icon="ℹ️"
        )
        return

    # Header Card for Current Resume
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #F8FAFC, #EFF6FF); border: 1px solid #BFDBFE; border-radius: 14px; padding: 1.25rem; margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div>
                <span style="font-size: 0.75rem; font-weight: 700; color: #2563EB; text-transform: uppercase; letter-spacing: 0.05em;">● Active Resume Profile</span>
                <h3 style="margin: 4px 0 2px 0; color: #0F172A; font-size: 1.2rem;">{existing_resume.get('file_name', 'Resume')}</h3>
                <span style="font-size: 0.8rem; color: #64748B;">Uploaded: {str(existing_resume.get('uploaded_at', ''))[:16]}</span>
            </div>
            <div style="display: flex; gap: 8px;">
                <span style="background: #DCFCE7; color: #166534; font-size: 0.8rem; font-weight: 700; padding: 4px 10px; border-radius: 8px;">
                    ✓ Parsed & Ready
                </span>
            </div>
        </div>
        <div style="margin-top: 0.85rem; font-size: 0.88rem; color: #334155; line-height: 1.55; border-top: 1px solid #DBEAFE; padding-top: 0.75rem;">
            <b>Executive Summary:</b> {existing_resume.get('summary', 'No summary available.')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Action Row
    col_act1, col_act2, col_act3 = st.columns([2, 1.2, 1.2])
    with col_act1:
        if st.button("🎙️ Start Resume-Based Mock Interview", type="primary", width="stretch"):
            st.session_state["active_page"] = "interview"
            st.session_state["use_resume_mode"] = True
            st.rerun()
    with col_act2:
        with st.popover("👁️ View Extracted Text"):
            st.caption("Raw text extracted from your document for AI processing:")
            st.text_area("Extracted Text", existing_resume.get("raw_text", ""), height=300)
    with col_act3:
        if st.button("🗑️ Delete Resume", width="stretch", help="Permanently removes resume data"):
            delete_candidate_resume(user_id)
            st.success("Resume deleted permanently.")
            st.rerun()

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # 3. Skills & Competencies Grid
    col_skills, col_edu = st.columns([1.6, 1])

    with col_skills:
        st.markdown("#### 🛠️ Identified Technical Skills")
        skills = existing_resume.get("parsed_skills", [])
        if skills:
            # Render skills as clean badges
            skill_badges = " ".join([
                f'<span style="display: inline-block; background: #EEF2FF; color: #4338CA; border: 1px solid #C7D2FE; font-weight: 600; font-size: 0.82rem; padding: 4px 10px; border-radius: 20px; margin: 3px 2px;">{s}</span>'
                for s in skills
            ])
            st.markdown(f'<div style="line-height: 2.2;">{skill_badges}</div>', unsafe_allow_html=True)
        else:
            st.caption("No specific skills identified.")

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

        st.markdown("#### 💻 Extracted Projects")
        projects = existing_resume.get("parsed_projects", [])
        if projects:
            for p in projects:
                p_title = p.get("title", "Project") if isinstance(p, dict) else str(p)
                p_tech = p.get("tech", "") if isinstance(p, dict) else ""
                p_desc = p.get("description", "") if isinstance(p, dict) else ""
                st.markdown(f"""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 0.85rem; margin-bottom: 0.6rem;">
                    <div style="font-weight: 700; color: #0F172A; font-size: 0.92rem;">📁 {p_title}</div>
                    {f'<div style="font-size: 0.78rem; color: #4F46E5; font-weight: 600; margin-top: 2px;">Tech: {p_tech}</div>' if p_tech else ''}
                    <div style="font-size: 0.82rem; color: #475569; margin-top: 4px; line-height: 1.45;">{p_desc}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("No projects identified.")

    with col_edu:
        st.markdown("#### 🎓 Education & Background")
        education = existing_resume.get("parsed_education", [])
        if education:
            for edu in education:
                degree = edu.get("degree", "Degree") if isinstance(edu, dict) else str(edu)
                college = edu.get("college", "University") if isinstance(edu, dict) else ""
                score = edu.get("score", "") if isinstance(edu, dict) else ""
                year = edu.get("graduation_year", "") if isinstance(edu, dict) else ""
                st.markdown(f"""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 0.85rem; margin-bottom: 0.6rem;">
                    <div style="font-weight: 700; color: #0F172A; font-size: 0.9rem;">{degree}</div>
                    <div style="font-size: 0.8rem; color: #64748B; margin-top: 2px;">🏛️ {college}</div>
                    <div style="display: flex; gap: 10px; font-size: 0.78rem; color: #0F172A; font-weight: 600; margin-top: 4px;">
                        <span>📅 Class of {year}</span>
                        {f'<span>• 🎯 {score}</span>' if score else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("No education parsed.")

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        st.markdown("#### 💼 Work & Internships")
        experience = existing_resume.get("parsed_experience", [])
        if experience:
            for exp in experience:
                role = exp.get("role", "Role") if isinstance(exp, dict) else str(exp)
                comp = exp.get("company", "Company") if isinstance(exp, dict) else ""
                dur = exp.get("duration", "") if isinstance(exp, dict) else ""
                st.markdown(f"""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 0.85rem; margin-bottom: 0.6rem;">
                    <div style="font-weight: 700; color: #0F172A; font-size: 0.9rem;">{role}</div>
                    <div style="font-size: 0.8rem; color: #475569;">🏢 {comp} {f'({dur})' if dur else ''}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("No work experience listed.")

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # 4. Strengths vs Missing Skills
    col_str, col_miss = st.columns(2)

    with col_str:
        st.markdown("#### 🏆 Confirmed Strengths")
        strengths = existing_resume.get("strengths", [])
        if strengths:
            for s in strengths:
                st.markdown(f"""
                <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.5rem; font-size: 0.85rem; color: #166534; font-weight: 600;">
                    ✓ {s}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("No specific strengths detected.")

    with col_miss:
        st.markdown("#### ⚠️ Missing / Recommended Competencies")
        missing = existing_resume.get("missing_skills", [])
        if missing:
            for m in missing:
                st.markdown(f"""
                <div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.5rem; font-size: 0.85rem; color: #991B1B; font-weight: 600;">
                    ⚠️ {m}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Profile appears well-rounded.")

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # 5. Suggested Improvements & Tailored Questions
    col_tips, col_q = st.columns(2)

    with col_tips:
        st.markdown("#### 💡 Resume Improvement Tips (Placement ATS)")
        tips = existing_resume.get("suggested_improvements", [])
        if tips:
            for i, tip in enumerate(tips, 1):
                st.markdown(f"""
                <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.5rem; font-size: 0.85rem; color: #92400E;">
                    <b>{i}.</b> {tip}
                </div>
                """, unsafe_allow_html=True)

    with col_q:
        st.markdown("#### 🎯 Potential Interview Questions (From Resume)")
        questions = existing_resume.get("interview_questions", [])
        if questions:
            for i, q in enumerate(questions, 1):
                st.markdown(f"""
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.5rem; font-size: 0.85rem; color: #0F172A;">
                    <span style="font-weight: 700; color: #4F46E5;">Q{i}:</span> {q}
                </div>
                """, unsafe_allow_html=True)
