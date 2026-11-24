import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import (
    save_candidate_resume,
    get_candidate_resume,
    delete_candidate_resume,
    create_interview_session,
    record_question_and_feedback,
    finalize_interview_session,
    delete_interview_session,
    save_roadmap_with_tasks,
    get_user_roadmaps,
    get_roadmap_by_id,
    toggle_roadmap_task,
    delete_roadmap,
    get_all_user_topics,
    update_topic_revision_status,
    delete_user_topic
)

def test_enhancements():
    # Create a real test user first
    from database import create_user, delete_user_account
    u, err = create_user("db_test_user", "db_test@test.edu.in", "Password@123", "DB Test User")
    assert u is not None, f"Failed to create test user: {err}"
    user_id = u["id"]

    # 1. Resume CRUD
    r_id = save_candidate_resume(
        user_id=user_id,
        file_name="resume.pdf",
        raw_text="Experienced Python and React developer",
        parsed_skills=["Python", "React", "Docker", "FastAPI"],
        parsed_projects=[{"title": "E-Commerce", "tech": "React, Python"}],
        parsed_experience=[{"role": "SDE Intern", "company": "Tech Corp"}],
        parsed_education=[{"degree": "B.Tech CSE", "college": "NIT"}],
        strengths=["Strong backend API design"],
        missing_skills=["Kubernetes", "GraphQL"],
        suggested_improvements=["Add metrics to project bullet points"],
        interview_questions=["How do you handle rate limiting in FastAPI?"],
        summary="Candidate with 1 year experience in full-stack web applications."
    )
    assert r_id > 0, "Resume save failed"

    fetched = get_candidate_resume(user_id)
    assert fetched is not None, "Resume fetch failed"
    assert "Python" in fetched["parsed_skills"], "Skills not parsed correctly"
    assert "Kubernetes" in fetched["missing_skills"], "Missing skills not parsed"
    assert fetched["summary"] != "", "Summary missing"

    # 2. Interview Session & Question CRUD
    s_id = create_interview_session(
        user_id=user_id,
        role_id="sde_fresher",
        role_title="Software Development Engineer (SDE-1)",
        difficulty="Intermediate",
        interview_type="Technical",
        target_company_track="Product Companies",
        duration_minutes=20
    )
    assert s_id > 0, "Session create failed"

    q_id = record_question_and_feedback(
        session_id=s_id,
        question_number=1,
        question_text="What is the difference between TCP and UDP?",
        category="Computer Networks",
        user_answer="TCP is connection oriented and reliable, UDP is connectionless and faster.",
        scores={"overall": 85.0, "accuracy": 90.0, "conceptual": 85.0, "relevance": 85.0, "completeness": 80.0, "clarity": 85.0},
        honest_feedback="Good fundamental understanding. Could mention 3-way handshake and packet loss.",
        incorrect_concepts="[]",
        missing_information='["3-way handshake details", "flow control via sliding window"]',
        improved_answer="TCP establishes a reliable connection using a 3-way handshake with flow control...",
        improvement_reason="Provides deeper mechanical details on protocol differences."
    )
    assert q_id > 0, "Question record failed"

    finalize_interview_session(
        session_id=s_id,
        summary="Solid networking knowledge.",
        overall_score=85.0,
        accuracy_score=90.0,
        relevance_score=85.0,
        completeness_score=80.0,
        clarity_score=85.0,
        conceptual_score=85.0,
        readiness_assessment="Placement Ready"
    )

    # 3. Roadmap & Tasks CRUD
    tasks = [
        {
            "day": 1,
            "focus_topic": "Dynamic Programming",
            "core_concept_to_master": "Memoization vs Tabulation",
            "recommended_study": "Read NeetCode 150 DP guide",
            "practical_exercise": "Climbing Stairs, House Robber",
            "hours_recommended": 3
        },
        {
            "day": 2,
            "focus_topic": "Graphs & BFS",
            "core_concept_to_master": "Queue based traversal and cycle detection",
            "recommended_study": "Graph representation using adjacency lists",
            "practical_exercise": "Number of Islands",
            "hours_recommended": 3
        }
    ]
    roadmap_id = save_roadmap_with_tasks(
        user_id=user_id,
        title="14-Day SDE-1 Placement Sprint",
        target_role="Software Development Engineer (SDE-1)",
        duration_days=14,
        weak_topics_covered="DP, Graphs",
        plan_content="Comprehensive daily schedule",
        daily_tasks=tasks
    )
    assert roadmap_id > 0, "Roadmap save failed"

    rm = get_roadmap_by_id(roadmap_id, user_id)
    assert rm is not None and len(rm["tasks"]) == 2, "Roadmap fetch with tasks failed"
    task_id = rm["tasks"][0]["id"]

    # Toggle task
    toggle_roadmap_task(task_id, True)
    rm_after = get_roadmap_by_id(roadmap_id, user_id)
    assert rm_after["tasks"][0]["is_completed"] == 1, "Task toggle failed"
    assert rm_after["progress_percent"] == 50, f"Expected 50% progress, got {rm_after['progress_percent']}"

    # 4. Clean up test data
    assert delete_interview_session(s_id, user_id), "Session delete failed"
    assert delete_candidate_resume(user_id), "Resume delete failed"
    assert delete_roadmap(roadmap_id, user_id), "Roadmap delete failed"
    assert delete_user_account(user_id), "User account delete failed"

    print("✔ All database enhancement tests passed!")

if __name__ == "__main__":
    test_enhancements()
