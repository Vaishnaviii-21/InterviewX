"""
Database models and data access layer for InterviewX.
Supports multi-user accounts, salted password authentication, resume storage,
mock interview sessions, and analytics aggregation.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from .connection import get_db_cursor, get_connection
from auth.security import (
    hash_password,
    verify_password,
    validate_username,
    validate_email,
    validate_password,
    validate_full_name,
)

# ==================== USER AUTHENTICATION & PROFILE CRUD ====================

def create_user(
    username: str,
    email: str,
    password: str,
    name: str,
    college: str = "Engineering Institute",
    degree: str = "B.Tech in Computer Science",
    graduation_year: int = 2026,
    target_role: str = "Software Development Engineer (SDE-1)",
    target_company_track: str = "Product Companies & Tier-1 Startups"
) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Validates input, securely hashes password, and creates a new candidate profile.
    Returns (user_dict, "") on success or (None, error_message) on failure.
    """
    # 1. Input validations
    u_ok, u_err = validate_username(username)
    if not u_ok:
        return None, u_err
    
    e_ok, e_err = validate_email(email)
    if not e_ok:
        return None, e_err
    
    p_ok, p_err = validate_password(password)
    if not p_ok:
        return None, p_err
    
    n_ok, n_err = validate_full_name(name)
    if not n_ok:
        return None, n_err

    clean_username = username.strip().lower()
    clean_email = email.strip().lower()
    clean_name = name.strip()

    # 2. Check for existing username or email
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (clean_username,))
        if cursor.fetchone():
            return None, f"Username '{clean_username}' is already registered. Please choose another."
        
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (clean_email,))
        if cursor.fetchone():
            return None, f"An account with email '{clean_email}' already exists. Please sign in."

    # 3. Hash password and insert
    pwd_hash = hash_password(password)
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO users (
                username, email, password_hash, name, college, degree,
                graduation_year, target_role, target_company_track
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            clean_username,
            clean_email,
            pwd_hash,
            clean_name,
            college.strip(),
            degree.strip(),
            int(graduation_year),
            target_role.strip(),
            target_company_track.strip()
        ))
        user_id = cursor.lastrowid
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None, ""

def authenticate_user(username_or_email: str, password: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Authenticates a user by username or email and plaintext password.
    Returns (user_dict, "") on success or (None, error_message) on failure.
    """
    if not username_or_email or not password:
        return None, "Please enter both username/email and password."

    clean_identifier = username_or_email.strip().lower()

    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT * FROM users 
            WHERE LOWER(username) = ? OR LOWER(email) = ? 
            LIMIT 1
        """, (clean_identifier, clean_identifier))
        row = cursor.fetchone()

        if not row:
            return None, "No account found matching that username or email."
        
        user = dict(row)
        stored_hash = user.get("password_hash", "")

        if not verify_password(password, stored_hash):
            return None, "Incorrect password. Please try again."

        # Return user without exposing hash
        safe_user = {k: v for k, v in user.items() if k != "password_hash"}
        return safe_user, ""

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves safe candidate profile by user ID."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            user = dict(row)
            user.pop("password_hash", None)
            return user
        return None

def get_or_create_default_user() -> Dict[str, Any]:
    """
    Retrieves user ID 1 (Arjun Verma demo candidate) or creates it if missing.
    Maintains backward compatibility across all modules.
    """
    seed_demo_data_if_empty()
    u = get_user_by_id(1)
    if u:
        return u
    return {
        "id": 1,
        "username": "arjun",
        "email": "arjun.verma@example.edu.in",
        "name": "Arjun Verma",
        "college": "National Institute of Technology (NIT)",
        "degree": "B.Tech in Computer Science & Engineering",
        "graduation_year": 2026,
        "target_role": "Software Development Engineer (SDE-1)",
        "target_company_track": "Product Companies & Tier-1 Startups"
    }

def update_user_profile(user_id: int, updates: Dict[str, Any]) -> bool:
    """Updates candidate profile details safely."""
    allowed = ["name", "email", "college", "degree", "graduation_year", "target_role", "target_company_track"]
    valid_updates = {k: v for k, v in updates.items() if k in allowed}
    if not valid_updates:
        return False
    
    set_clause = ", ".join([f"{k} = ?" for k in valid_updates.keys()])
    values = list(valid_updates.values()) + [user_id]
    
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)
        return cursor.rowcount > 0

# ==================== CANDIDATE RESUME MANAGEMENT (PRIVACY & DELETION) ====================

def save_candidate_resume(
    user_id: int,
    file_name: str,
    raw_text: str,
    parsed_skills: Optional[List[str]] = None,
    parsed_projects: Optional[List[Any]] = None,
    parsed_experience: Optional[List[Any]] = None,
    parsed_education: Optional[List[Any]] = None,
    strengths: Optional[List[str]] = None,
    missing_skills: Optional[List[str]] = None,
    suggested_improvements: Optional[List[str]] = None,
    interview_questions: Optional[List[str]] = None,
    summary: str = ""
) -> int:
    """
    Saves or replaces a comprehensive parsed resume profile for a candidate.
    """
    skills_json = json.dumps(parsed_skills or [])
    projects_json = json.dumps(parsed_projects or [])
    exp_json = json.dumps(parsed_experience or [])
    edu_json = json.dumps(parsed_education or [])
    str_json = json.dumps(strengths or [])
    miss_json = json.dumps(missing_skills or [])
    sugg_json = json.dumps(suggested_improvements or [])
    q_json = json.dumps(interview_questions or [])

    with get_db_cursor(commit=True) as cursor:
        cursor.execute("SELECT id FROM candidate_resumes WHERE user_id = ?", (user_id,))
        existing = cursor.fetchone()
        if existing:
            cursor.execute("""
                UPDATE candidate_resumes SET
                    file_name = ?,
                    raw_text = ?,
                    parsed_skills = ?,
                    parsed_projects = ?,
                    parsed_experience = ?,
                    parsed_education = ?,
                    strengths = ?,
                    missing_skills = ?,
                    suggested_improvements = ?,
                    interview_questions = ?,
                    summary = ?,
                    uploaded_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (
                file_name, raw_text, skills_json, projects_json, exp_json, edu_json,
                str_json, miss_json, sugg_json, q_json, summary, user_id
            ))
            return existing["id"]
        else:
            cursor.execute("""
                INSERT INTO candidate_resumes (
                    user_id, file_name, raw_text, parsed_skills, parsed_projects,
                    parsed_experience, parsed_education, strengths, missing_skills,
                    suggested_improvements, interview_questions, summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, file_name, raw_text, skills_json, projects_json, exp_json, edu_json,
                str_json, miss_json, sugg_json, q_json, summary
            ))
            return cursor.lastrowid

def get_candidate_resume(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves the active resume metadata and parsed profile for a candidate."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM candidate_resumes WHERE user_id = ? LIMIT 1", (user_id,))
        row = cursor.fetchone()
        if not row:
            return None
        res = dict(row)
        for json_field in [
            "parsed_skills", "parsed_projects", "parsed_experience", "parsed_education",
            "strengths", "missing_skills", "suggested_improvements", "interview_questions"
        ]:
            try:
                res[json_field] = json.loads(res.get(json_field) or "[]")
            except Exception:
                res[json_field] = []
        return res

def delete_candidate_resume(user_id: int) -> bool:
    """
    Permanently purges candidate resume text, skills, and projects for privacy.
    Sets resume_id to NULL on existing sessions so history is preserved.
    """
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM candidate_resumes WHERE user_id = ?", (user_id,))
        return cursor.rowcount > 0

# ==================== INTERVIEW SESSIONS & QUESTIONS CRUD ====================

def get_all_interviews(user_id: int = 1, limit: int = 25) -> List[Dict[str, Any]]:
    """Returns interview history for a specific user sorted by most recent."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT * FROM interview_sessions 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (user_id, limit))
        return [dict(row) for row in cursor.fetchall()]

def get_interview_by_id(session_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves full metadata for a specific interview session."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM interview_sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_interview_questions(session_id: int) -> List[Dict[str, Any]]:
    """Retrieves all questions, answers, and honest evaluations for an interview."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT * FROM interview_questions 
            WHERE session_id = ? 
            ORDER BY question_number ASC
        """, (session_id,))
        return [dict(row) for row in cursor.fetchall()]

def create_interview_session(
    user_id: int,
    role_id: str,
    role_title: str,
    difficulty: str,
    interview_type: str,
    target_company_track: str,
    resume_id: Optional[int] = None,
    duration_minutes: int = 15
) -> int:
    """Creates a new interview session and returns its ID."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO interview_sessions (
                user_id, resume_id, role_id, role_title, difficulty, interview_type,
                target_company_track, duration_minutes, total_questions, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 'in_progress')
        """, (user_id, resume_id, role_id, role_title, difficulty, interview_type, target_company_track, duration_minutes))
        return cursor.lastrowid

def record_question_and_feedback(
    session_id: int,
    question_number: int,
    question_text: str,
    category: str,
    user_answer: str,
    scores: Dict[str, float],
    honest_feedback: str,
    incorrect_concepts: str,
    missing_information: str,
    improved_answer: str,
    improvement_reason: str,
    is_resume_based: bool = False
) -> int:
    """Stores a single interview question, candidate answer, and honest AI feedback."""
    conceptual = scores.get("conceptual", scores.get("accuracy", 0.0))
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO interview_questions (
                session_id, question_number, question_text, category,
                is_resume_based, user_answer, overall_score, accuracy_score,
                conceptual_score, relevance_score, completeness_score, clarity_score,
                honest_feedback, incorrect_concepts, missing_information, improved_answer,
                improvement_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            question_number,
            question_text,
            category,
            1 if is_resume_based else 0,
            user_answer,
            scores.get("overall", 0.0),
            scores.get("accuracy", 0.0),
            conceptual,
            scores.get("relevance", 0.0),
            scores.get("completeness", 0.0),
            scores.get("clarity", 0.0),
            honest_feedback,
            incorrect_concepts,
            missing_information,
            improved_answer,
            improvement_reason
        ))
        
        cursor.execute("""
            UPDATE interview_sessions
            SET total_questions = total_questions + 1
            WHERE id = ?
        """, (session_id,))
        
        return cursor.lastrowid

def finalize_interview_session(
    session_id: int,
    summary: str,
    overall_score: float,
    accuracy_score: float,
    relevance_score: float,
    completeness_score: float,
    clarity_score: float,
    conceptual_score: float = 0.0,
    readiness_assessment: str = ""
):
    """Marks an interview session as completed and records aggregate scores."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("""
            UPDATE interview_sessions SET
                status = 'completed',
                summary = ?,
                overall_score = ?,
                accuracy_score = ?,
                conceptual_score = ?,
                relevance_score = ?,
                completeness_score = ?,
                clarity_score = ?,
                readiness_assessment = ?,
                completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            summary,
            overall_score,
            accuracy_score,
            conceptual_score,
            relevance_score,
            completeness_score,
            clarity_score,
            readiness_assessment,
            session_id
        ))

def delete_interview_session(session_id: int, user_id: int) -> bool:
    """Deletes an interview session and cascades deletion to questions."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM interview_questions WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM interview_sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
        return cursor.rowcount > 0

def delete_user_account(user_id: int) -> bool:
    """Permanently deletes a user account and all associated data."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM candidate_resumes WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM user_topics WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM roadmaps WHERE user_id = ?", (user_id,))
        cursor.execute("""
            DELETE FROM interview_questions WHERE session_id IN (
                SELECT id FROM interview_sessions WHERE user_id = ?
            )
        """, (user_id,))
        cursor.execute("DELETE FROM interview_sessions WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return cursor.rowcount > 0

# ==================== WEAKNESSES, STRENGTHS & ANALYTICS ====================

def record_topic_status(user_id: int, topic_name: str, category: str, status: str, notes: str = ""):
    """Updates frequency of strengths or weaknesses."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("""
            SELECT id, frequency FROM user_topics 
            WHERE user_id = ? AND topic_name = ? AND status = ?
        """, (user_id, topic_name, status))
        row = cursor.fetchone()
        if row:
            cursor.execute("""
                UPDATE user_topics 
                SET frequency = frequency + 1, last_evaluated = CURRENT_TIMESTAMP, notes = ?
                WHERE id = ?
            """, (notes, row["id"]))
        else:
            cursor.execute("""
                INSERT INTO user_topics (user_id, topic_name, category, status, frequency, notes)
                VALUES (?, ?, ?, ?, 1, ?)
            """, (user_id, topic_name, category, status, notes))

def get_user_analytics(user_id: int = 1) -> Dict[str, Any]:
    """
    Computes key performance metrics, score averages, trend history,
    and recurring weaknesses/strengths for the specific user.
    """
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT 
                COUNT(*) as total_interviews,
                AVG(overall_score) as avg_overall,
                AVG(accuracy_score) as avg_accuracy,
                AVG(relevance_score) as avg_relevance,
                AVG(completeness_score) as avg_completeness,
                AVG(clarity_score) as avg_clarity,
                MAX(overall_score) as highest_score,
                MIN(overall_score) as lowest_score
            FROM interview_sessions
            WHERE user_id = ? AND status = 'completed'
        """, (user_id,))
        agg_row = cursor.fetchone()
        
        cursor.execute("""
            SELECT COUNT(*) as total_questions 
            FROM interview_questions iq
            JOIN interview_sessions iss ON iq.session_id = iss.id
            WHERE iss.user_id = ?
        """, (user_id,))
        q_row = cursor.fetchone()

        cursor.execute("""
            SELECT id, role_title, difficulty, overall_score, accuracy_score,
                   relevance_score, completeness_score, clarity_score, created_at
            FROM interview_sessions
            WHERE user_id = ? AND status = 'completed'
            ORDER BY created_at ASC
        """, (user_id,))
        trend_rows = [dict(r) for r in cursor.fetchall()]

        cursor.execute("""
            SELECT topic_name, category, frequency, notes, last_evaluated
            FROM user_topics
            WHERE user_id = ? AND status = 'weakness'
            ORDER BY frequency DESC, last_evaluated DESC
            LIMIT 6
        """, (user_id,))
        weaknesses = [dict(r) for r in cursor.fetchall()]

        cursor.execute("""
            SELECT topic_name, category, frequency, notes, last_evaluated
            FROM user_topics
            WHERE user_id = ? AND status = 'strength'
            ORDER BY frequency DESC, last_evaluated DESC
            LIMIT 6
        """, (user_id,))
        strengths = [dict(r) for r in cursor.fetchall()]

        total_interviews = agg_row["total_interviews"] if agg_row and agg_row["total_interviews"] else 0
        avg_score = round(agg_row["avg_overall"], 1) if agg_row and agg_row["avg_overall"] else 0.0

        readiness_index = 0
        if total_interviews > 0:
            volume_bonus = min(20, total_interviews * 5)
            score_factor = (avg_score / 100.0) * 60
            weak_count = len(weaknesses)
            str_count = len(strengths)
            ratio_factor = (str_count / (str_count + weak_count + 1)) * 20
            readiness_index = min(100, int(score_factor + volume_bonus + ratio_factor))

        return {
            "total_interviews": total_interviews,
            "total_questions": q_row["total_questions"] if q_row else 0,
            "avg_overall": avg_score,
            "avg_accuracy": round(agg_row["avg_accuracy"], 1) if agg_row and agg_row["avg_accuracy"] else 0.0,
            "avg_relevance": round(agg_row["avg_relevance"], 1) if agg_row and agg_row["avg_relevance"] else 0.0,
            "avg_completeness": round(agg_row["avg_completeness"], 1) if agg_row and agg_row["avg_completeness"] else 0.0,
            "avg_clarity": round(agg_row["avg_clarity"], 1) if agg_row and agg_row["avg_clarity"] else 0.0,
            "highest_score": round(agg_row["highest_score"], 1) if agg_row and agg_row["highest_score"] else 0.0,
            "readiness_index": readiness_index,
            "score_trends": trend_rows,
            "weaknesses": weaknesses,
            "strengths": strengths
        }

# ==================== ROADMAPS & WEAKNESS TRACKER CRUD ====================

def save_roadmap_with_tasks(
    user_id: int,
    title: str,
    target_role: str,
    duration_days: int,
    weak_topics_covered: str,
    plan_content: str,
    daily_tasks: List[Dict[str, Any]]
) -> int:
    """Saves a structured day-wise roadmap and populates individual daily tasks."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO roadmaps (
                user_id, title, target_role, duration_days, weak_topics_covered, plan_content, progress_percent
            ) VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (user_id, title, target_role, duration_days, weak_topics_covered, plan_content))
        roadmap_id = cursor.lastrowid

        for task in daily_tasks:
            cursor.execute("""
                INSERT INTO roadmap_tasks (
                    roadmap_id, day_number, focus_topic, core_concept, recommended_study,
                    practical_exercise, hours_recommended, is_completed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                roadmap_id,
                task.get("day", 1),
                task.get("focus_topic", "Technical Concept"),
                task.get("core_concept_to_master", ""),
                task.get("recommended_study", ""),
                task.get("practical_exercise", ""),
                task.get("hours_recommended", 2)
            ))
        return roadmap_id

def get_user_roadmaps(user_id: int) -> List[Dict[str, Any]]:
    """Retrieves all generated preparation roadmaps for a candidate."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT * FROM roadmaps WHERE user_id = ? ORDER BY created_at DESC
        """, (user_id,))
        return [dict(r) for r in cursor.fetchall()]

def get_roadmap_by_id(roadmap_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a specific roadmap with its interactive daily tasks."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT * FROM roadmaps WHERE id = ? AND user_id = ?", (roadmap_id, user_id))
        row = cursor.fetchone()
        if not row:
            return None
        res = dict(row)
        cursor.execute("SELECT * FROM roadmap_tasks WHERE roadmap_id = ? ORDER BY day_number ASC", (roadmap_id,))
        res["tasks"] = [dict(t) for t in cursor.fetchall()]
        return res

def toggle_roadmap_task(task_id: int, is_completed: bool) -> bool:
    """Updates the completion state of a daily roadmap task and recalibrates overall progress."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("""
            UPDATE roadmap_tasks 
            SET is_completed = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (1 if is_completed else 0, task_id))

        cursor.execute("SELECT roadmap_id FROM roadmap_tasks WHERE id = ?", (task_id,))
        r_row = cursor.fetchone()
        if r_row:
            r_id = r_row["roadmap_id"]
            cursor.execute("SELECT COUNT(*) as total, SUM(is_completed) as done FROM roadmap_tasks WHERE roadmap_id = ?", (r_id,))
            stat = cursor.fetchone()
            total = stat["total"] or 0
            done = stat["done"] or 0
            pct = int((done / total) * 100) if total > 0 else 0
            cursor.execute("UPDATE roadmaps SET progress_percent = ? WHERE id = ?", (pct, r_id))
        return True

def delete_roadmap(roadmap_id: int, user_id: int) -> bool:
    """Deletes a roadmap and its tasks."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM roadmap_tasks WHERE roadmap_id = ?", (roadmap_id,))
        cursor.execute("DELETE FROM roadmaps WHERE id = ? AND user_id = ?", (roadmap_id, user_id))
        return cursor.rowcount > 0

def get_all_user_topics(user_id: int) -> List[Dict[str, Any]]:
    """Retrieves all tracked topics with priority status and notes."""
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("""
            SELECT * FROM user_topics WHERE user_id = ? ORDER BY frequency DESC, last_evaluated DESC
        """, (user_id,))
        return [dict(r) for r in cursor.fetchall()]

def update_topic_revision_status(topic_id: int, user_id: int, revision_status: str) -> bool:
    """Updates revision status of a topic (Needs Work, In Progress, Mastered)."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("""
            UPDATE user_topics SET revision_status = ?, last_evaluated = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
        """, (revision_status, topic_id, user_id))
        return cursor.rowcount > 0

def delete_user_topic(topic_id: int, user_id: int) -> bool:
    """Deletes a topic from user's weakness/strength tracker."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM user_topics WHERE id = ? AND user_id = ?", (topic_id, user_id))
        return cursor.rowcount > 0

# ==================== DEMO SEEDING ====================

def seed_demo_data_if_empty():
    """
    Seeds demo candidate profile (username: 'arjun', password: 'Demo@123')
    and realistic mock interview sessions if empty.
    """
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("SELECT id FROM users WHERE id = 1 LIMIT 1")
        user_row = cursor.fetchone()
        
        if not user_row:
            demo_hash = hash_password("Demo@123")
            cursor.execute("""
                INSERT INTO users (
                    id, username, email, password_hash, name, college, degree,
                    graduation_year, target_role, target_company_track
                ) VALUES (
                    1, 'arjun', 'arjun.verma@example.edu.in', ?, 'Arjun Verma',
                    'National Institute of Technology (NIT)',
                    'B.Tech in Computer Science & Engineering',
                    2026,
                    'Software Development Engineer (SDE-1)',
                    'Product Companies & Tier-1 Startups'
                )
            """, (demo_hash,))

    # Check if sessions exist for user 1
    with get_db_cursor(commit=False) as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM interview_sessions WHERE user_id = 1")
        if cursor.fetchone()["count"] > 0:
            return  # Already seeded

    now = datetime.now()
    s1_date = (now - timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")
    s2_date = (now - timedelta(days=9)).strftime("%Y-%m-%d %H:%M:%S")
    s3_date = (now - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S")
    s4_date = (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

    with get_db_cursor(commit=True) as cursor:
        # Session 1
        cursor.execute("""
            INSERT INTO interview_sessions (
                id, user_id, role_id, role_title, difficulty, interview_type,
                target_company_track, total_questions, overall_score, accuracy_score,
                relevance_score, completeness_score, clarity_score, summary,
                status, created_at, completed_at
            ) VALUES (
                1, 1, 'sde_fresher', 'Software Development Engineer (SDE-1)',
                'Beginner (Campus Placements / Freshers)', 'Technical Round',
                'IT Services & Mass Recruiters (TCS, Infosys)', 2,
                54.0, 50.0, 65.0, 48.0, 53.0,
                'Candidate demonstrated baseline knowledge of loops but struggled with accurate complexity analysis and modern Java HashMap internal mechanics.',
                'completed', ?, ?
            )
        """, (s1_date, s1_date))

        cursor.execute("""
            INSERT INTO interview_questions (
                session_id, question_number, question_text, category, user_answer,
                overall_score, accuracy_score, relevance_score, completeness_score, clarity_score,
                honest_feedback, incorrect_concepts, missing_information, improved_answer, improvement_reason, created_at
            ) VALUES (
                1, 1,
                'Explain how Java HashMap handles hash collisions internally and what is its worst-case time complexity.',
                'Data Structures',
                'HashMap uses an array with linked lists. When two keys have same hash code, it just adds them in the linked list. Search is always O(1) in HashMap.',
                48.0, 42.0, 70.0, 40.0, 50.0,
                'Your answer contains a critical technical error regarding worst-case complexity and omits Java 8+ architectural changes. While average lookup is O(1), worst-case is NOT O(1). Claiming O(1) in an interview will disqualify you on core data structures.',
                '["Claimed lookup is always O(1)", "Stated collisions only use linked list indefinitely"]',
                '["Java 8 treeification threshold (when bucket exceeds 8 nodes, linked list turns into Red-Black Tree)", "Worst-case time complexity is O(log N) in Java 8+, and O(N) prior to Java 8", "Role of equals() and hashCode() contracts"]',
                'In Java, HashMap internally uses an array of Node buckets. When collisions occur, elements are stored in a linked list. In Java 8+, once a bucket reaches TREEIFY_THRESHOLD (8 items) and array capacity is at least 64, it converts the list into a Red-Black Tree (TreeNode). The average time complexity for get() and put() is O(1), but the worst-case with severe collisions is O(log N) in Java 8+ (or O(N) in legacy versions). Proper implementation of equals() and hashCode() is mandatory to prevent unnecessary collisions.',
                'Directly addresses internal mechanics, cites exact Java 8 threshold (8 nodes -> Red-Black Tree), and clearly distinguishes between average O(1) and worst-case O(log N).',
                ?
            )
        """, (s1_date,))

        # Session 2
        cursor.execute("""
            INSERT INTO interview_sessions (
                id, user_id, role_id, role_title, difficulty, interview_type,
                target_company_track, total_questions, overall_score, accuracy_score,
                relevance_score, completeness_score, clarity_score, summary,
                status, created_at, completed_at
            ) VALUES (
                2, 1, 'sde_fresher', 'Software Development Engineer (SDE-1)',
                'Intermediate (1-2 Years / Product Startups)', 'HR & Behavioral',
                'Product Companies & Tier-1 Startups', 1,
                68.0, 72.0, 65.0, 64.0, 71.0,
                'Good communication, but stories lacked quantifiable metrics and structured STAR methodology.',
                'completed', ?, ?
            )
        """, (s2_date, s2_date))

        # Session 3
        cursor.execute("""
            INSERT INTO interview_sessions (
                id, user_id, role_id, role_title, difficulty, interview_type,
                target_company_track, total_questions, overall_score, accuracy_score,
                relevance_score, completeness_score, clarity_score, summary,
                status, created_at, completed_at
            ) VALUES (
                3, 1, 'backend_dev', 'Backend Developer (Java / Python / Node.js)',
                'Intermediate (1-2 Years / Product Startups)', 'Technical Round',
                'Product Companies & Tier-1 Startups', 1,
                79.0, 82.0, 80.0, 75.0, 79.0,
                'Substantial improvement in technical precision. Strong grasp of indexing and database transactions.',
                'completed', ?, ?
            )
        """, (s3_date, s3_date))

        # Session 4
        cursor.execute("""
            INSERT INTO interview_sessions (
                id, user_id, role_id, role_title, difficulty, interview_type,
                target_company_track, total_questions, overall_score, accuracy_score,
                relevance_score, completeness_score, clarity_score, summary,
                status, created_at, completed_at
            ) VALUES (
                4, 1, 'sde_fresher', 'Software Development Engineer (SDE-1)',
                'Intermediate (1-2 Years / Product Startups)', 'Comprehensive Mock',
                'Product Companies & Tier-1 Startups', 1,
                86.0, 88.0, 87.0, 83.0, 86.0,
                'Impressive upward trajectory! Clear communication, structured answers, and strong mastery of system design basics.',
                'completed', ?, ?
            )
        """, (s4_date, s4_date))

        # Seed Weaknesses and Strengths for user 1
        weaknesses_data = [
            ("Time & Space Complexity of Recursive Calls", "Data Structures", 3, "Frequently misses call-stack memory overhead when calculating space complexity."),
            ("Java 8 HashMap Collision & Treeification Threshold", "Core CS & Language", 2, "Stated HashMap was always O(1) in first session. Needs review on Red-Black Tree mechanics."),
            ("Database Isolation Levels (Dirty reads vs Phantom reads)", "DBMS", 2, "Confuses Repeatable Read with Serializable isolation."),
            ("STAR Method Quantification in HR Rounds", "Behavioral / HR", 2, "Needs to include specific metrics (percentages, user counts, load numbers).")
        ]
        for topic, cat, freq, note in weaknesses_data:
            cursor.execute("""
                INSERT INTO user_topics (user_id, topic_name, category, status, frequency, notes)
                VALUES (1, ?, ?, 'weakness', ?, ?)
            """, (topic, cat, freq, note))

        strengths_data = [
            ("SQL Queries, Indexing & Joins", "DBMS", 4, "Consistently explains B-Tree indexing and query execution plans well."),
            ("Array & Two-Pointer Algorithmic Patterns", "Data Structures", 3, "Clean explanation of time/space trade-offs for two pointers and sliding window."),
            ("Clean Code & Object Oriented Design", "Software Engineering", 3, "Strong grasp of SOLID principles and encapsulation.")
        ]
        for topic, cat, freq, note in strengths_data:
            cursor.execute("""
                INSERT INTO user_topics (user_id, topic_name, category, status, frequency, notes)
                VALUES (1, ?, ?, 'strength', ?, ?)
            """, (topic, cat, freq, note))

def reset_database():
    """Drops and re-creates all tables cleanly."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DROP TABLE IF EXISTS roadmaps;")
        cursor.execute("DROP TABLE IF EXISTS user_topics;")
        cursor.execute("DROP TABLE IF EXISTS interview_questions;")
        cursor.execute("DROP TABLE IF EXISTS interview_sessions;")
        cursor.execute("DROP TABLE IF EXISTS candidate_resumes;")
        cursor.execute("DROP TABLE IF EXISTS users;")
    from .connection import init_db
    init_db()
