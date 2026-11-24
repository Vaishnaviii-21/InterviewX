import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.gemini_service import GeminiService
from database import (
    create_user,
    delete_user_account,
    create_interview_session,
    record_question_and_feedback,
    finalize_interview_session,
    get_interview_by_id,
    get_interview_questions
)

def test_interview_engine():
    print("--- TESTING AI MOCK INTERVIEW ENGINE ---")

    # 1. Test Question Generator
    svc = GeminiService()
    q1 = svc.generate_interview_question(
        role_title="Python Developer",
        difficulty="Intermediate",
        interview_type="Technical Interview",
        question_number=1,
        target_company_track="Product Companies & Tier-1 Startups"
    )
    assert "question_text" in q1, "Question text missing"
    assert "category" in q1, "Category missing"
    print(f"✔ Question 1 Generated: '{q1['question_text'][:60]}...' ({q1['category']})")

    # 2. Test Follow-Up Question Generator
    prev = [{"question_text": q1["question_text"], "user_answer": "I use list comprehension", "overall_score": 60.0}]
    q2 = svc.generate_interview_question(
        role_title="Python Developer",
        difficulty="Intermediate",
        interview_type="Technical Interview",
        question_number=2,
        target_company_track="Product Companies",
        previous_context=prev
    )
    assert "question_text" in q2, "Follow-up question text missing"
    print(f"✔ Follow-up Question 2 Generated: '{q2['question_text'][:60]}...'")

    # 3. Test Answer Evaluation (4 criteria out of 10)
    ans = "In Python, the GIL or Global Interpreter Lock is a mutex that prevents multiple threads from executing Python bytecodes at once. This means multithreading is limited for CPU bound tasks, so multiprocessing or Celery is used instead."
    eval_res = svc.evaluate_answer_honest(
        question_text=q1["question_text"],
        user_answer=ans,
        role_title="Python Developer",
        difficulty="Intermediate"
    )
    assert "scores_10" in eval_res or "scores" in eval_res, "Scores missing from evaluation"
    assert "honest_critique" in eval_res, "Honest critique missing"
    assert "improved_sample_answer" in eval_res, "Sample answer missing"
    print(f"✔ Evaluation Complete. Overall: {eval_res.get('scores', {}).get('overall')}%")

    # 4. Test Persistence Loop
    u, _ = create_user("engine_test_user", "engine_test@test.edu.in", "Password@123", "Engine Tester")
    user_id = u["id"]

    s_id = create_interview_session(
        user_id=user_id,
        role_id="python_developer",
        role_title="Python Developer",
        difficulty="Intermediate",
        interview_type="Technical Interview",
        target_company_track="Product Companies"
    )

    q_id = record_question_and_feedback(
        session_id=s_id,
        question_number=1,
        question_text=q1["question_text"],
        category=q1["category"],
        user_answer=ans,
        scores=eval_res.get("scores", {}),
        honest_feedback=eval_res.get("honest_critique", ""),
        incorrect_concepts=json.dumps(eval_res.get("incorrect_concepts", [])),
        missing_information=json.dumps(eval_res.get("missing_information", [])),
        improved_answer=eval_res.get("improved_sample_answer", ""),
        improvement_reason=eval_res.get("why_improved_is_better", "")
    )
    assert q_id > 0, "Question persistence failed"

    finalize_interview_session(
        session_id=s_id,
        summary="Engine test passed successfully.",
        overall_score=eval_res.get("scores", {}).get("overall", 75.0),
        accuracy_score=eval_res.get("scores", {}).get("accuracy", 75.0),
        relevance_score=eval_res.get("scores", {}).get("relevance", 75.0),
        completeness_score=eval_res.get("scores", {}).get("completeness", 75.0),
        clarity_score=eval_res.get("scores", {}).get("clarity", 75.0),
        conceptual_score=eval_res.get("scores", {}).get("conceptual", 75.0),
        readiness_assessment="Placement Ready"
    )

    sess = get_interview_by_id(s_id)
    assert sess["status"] == "completed", "Session status not updated"
    assert len(get_interview_questions(s_id)) == 1, "Recorded questions count mismatch"

    # Cleanup
    delete_user_account(user_id)
    print("🎉 ALL INTERVIEW ENGINE TESTS PASSED!")

if __name__ == "__main__":
    test_interview_engine()
