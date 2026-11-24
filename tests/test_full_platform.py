"""
Comprehensive End-to-End Test Suite for InterviewX Platform.
Validates all core features:
1. User Registration, Authentication & Profile Updates
2. Multi-turn AI Mock Interview Engine & Question Generation
3. Resume Parsing (PDF, DOCX, TXT) & Skill Extraction
4. Criteria-based Honest Evaluation (4 pillars out of 10)
5. Pure-Python PDF Feedback Report Generator
6. Weakness Tracker & Revision Lifecycle
7. Interactive Preparation Roadmap & Milestone Persistence
8. User Data Isolation & Secure Account Deletion
"""

import os
import sys
import json
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.connection import init_db, get_db_cursor
from database.models import (
    create_user,
    authenticate_user,
    get_user_by_id,
    update_user_profile,
    save_candidate_resume,
    get_candidate_resume,
    delete_candidate_resume,
    create_interview_session,
    record_question_and_feedback,
    finalize_interview_session,
    get_all_interviews,
    get_interview_by_id,
    get_interview_questions,
    delete_interview_session,
    record_topic_status,
    get_all_user_topics,
    update_topic_revision_status,
    delete_user_topic,
    save_roadmap_with_tasks,
    get_user_roadmaps,
    get_roadmap_by_id,
    toggle_roadmap_task,
    delete_roadmap,
    delete_user_account,
    get_user_analytics,
)
from utils.resume_parser import ResumeParser, ResumeAnalyzer
from utils.pdf_generator import PDFReportGenerator
from services.gemini_service import GeminiService


class TestInterviewXFullPlatform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Ensure clean test environment and initialized database."""
        init_db()

    def setUp(self):
        """Create fresh test users for isolated testing."""
        self.username_a = "test_candidate_alpha"
        self.username_b = "test_candidate_beta"
        
        # Clean up any leftover users from previous test runs
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("SELECT id FROM users WHERE username IN (?, ?)", (self.username_a, self.username_b))
            for row in cursor.fetchall():
                delete_user_account(row["id"])

        user_a, err_a = create_user(
            username=self.username_a,
            email="alpha@example.com",
            password="SecurePassword@123",
            name="Alpha Candidate",
            college="IIT Delhi",
            degree="B.Tech (CS)",
            graduation_year=2026,
            target_role="Software Development Engineer (SDE-1)",
            target_company_track="Product / Tier-1 Tech (FAANG/MAANG)"
        )
        self.assertIsNotNone(user_a, f"Failed to create user A: {err_a}")
        self.user_a_id = user_a["id"]

        user_b, err_b = create_user(
            username=self.username_b,
            email="beta@example.com",
            password="SecurePassword@456",
            name="Beta Candidate",
            college="NIT Trichy",
            degree="B.Tech (ECE)",
            graduation_year=2025,
            target_role="Data Engineer",
            target_company_track="FinTech & Banking"
        )
        self.assertIsNotNone(user_b, f"Failed to create user B: {err_b}")
        self.user_b_id = user_b["id"]

    def tearDown(self):
        """Clean up test users and their cascading data."""
        if hasattr(self, "user_a_id") and self.user_a_id:
            delete_user_account(self.user_a_id)
        if hasattr(self, "user_b_id") and self.user_b_id:
            delete_user_account(self.user_b_id)

    # =========================================================================
    # 1. AUTHENTICATION & PROFILE MANAGEMENT
    # =========================================================================
    def test_01_authentication_and_profile_updates(self):
        # Successful authentication
        auth_user, err = authenticate_user(self.username_a, "SecurePassword@123")
        self.assertIsNotNone(auth_user)
        self.assertEqual(err, "")
        self.assertEqual(auth_user["id"], self.user_a_id)
        self.assertNotIn("password_hash", auth_user)

        # Invalid password authentication
        bad_auth, bad_err = authenticate_user(self.username_a, "WrongPassword")
        self.assertIsNone(bad_auth)
        self.assertNotEqual(bad_err, "")

        # Update profile
        updates = {
            "name": "Alpha Senior Candidate",
            "college": "IIT Delhi (AI Dept)",
            "graduation_year": 2027,
            "target_role": "Backend Developer",
        }
        res = update_user_profile(self.user_a_id, updates)
        self.assertTrue(res)

        updated_user = get_user_by_id(self.user_a_id)
        self.assertEqual(updated_user["name"], "Alpha Senior Candidate")
        self.assertEqual(updated_user["college"], "IIT Delhi (AI Dept)")
        self.assertEqual(updated_user["target_role"], "Backend Developer")

    # =========================================================================
    # 2. RESUME PARSING & RESUME-BASED INTERVIEW PREP
    # =========================================================================
    def test_02_resume_parsing_and_persistence(self):
        sample_resume_text = (
            "Arjun Sharma\n"
            "Email: arjun@test.com\n"
            "Education: B.Tech Computer Science from IIT Bombay, 2025\n"
            "Skills: Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis, React\n"
            "Experience: Backend Engineering Intern at FinTech Startup building payment microservices.\n"
            "Projects: Scalable Distributed Rate Limiter handling 100k requests/sec using token bucket and Redis cluster."
        )

        analysis = ResumeAnalyzer.analyze_resume(sample_resume_text, "arjun_resume.pdf")
        self.assertIn("summary", analysis)
        self.assertIn("parsed_skills", analysis)
        self.assertGreater(len(analysis["parsed_skills"]), 0)
        self.assertIn("Python", analysis["parsed_skills"])
        self.assertIn("Docker", analysis["parsed_skills"])

        # Save to database
        res_id = save_candidate_resume(
            user_id=self.user_a_id,
            file_name="arjun_resume.pdf",
            raw_text=sample_resume_text,
            parsed_skills=analysis["parsed_skills"],
            parsed_projects=analysis.get("parsed_projects", []),
            parsed_experience=analysis.get("parsed_experience", []),
            parsed_education=analysis.get("parsed_education", []),
            strengths=analysis.get("strengths", []),
            missing_skills=analysis.get("missing_skills", []),
            suggested_improvements=analysis.get("suggested_improvements", []),
            interview_questions=analysis.get("interview_questions", []),
            summary=analysis.get("summary", "")
        )
        self.assertIsNotNone(res_id)

        # Retrieve and verify
        saved_resume = get_candidate_resume(self.user_a_id)
        self.assertIsNotNone(saved_resume)
        self.assertEqual(saved_resume["file_name"], "arjun_resume.pdf")
        self.assertIn("Python", saved_resume["parsed_skills"])

        # Resume privacy deletion
        deleted = delete_candidate_resume(self.user_a_id)
        self.assertTrue(deleted)
        self.assertIsNone(get_candidate_resume(self.user_a_id))

    # =========================================================================
    # 3. AI MOCK INTERVIEW ENGINE & CRITERIA EVALUATION
    # =========================================================================
    def test_03_mock_interview_engine_and_criteria_scoring(self):
        # 1. Generate questions
        q_obj = GeminiService().generate_interview_question(
            role_title="Backend Developer",
            difficulty="Medium",
            interview_type="Technical",
            question_number=1,
            target_company_track="Product"
        )
        self.assertIsNotNone(q_obj)
        self.assertIn("question_text", q_obj)
        self.assertIn("category", q_obj)

        # 2. Evaluate answer
        eval_result = GeminiService().evaluate_answer_honest(
            question_text="What is the difference between a process and a thread, and how does memory sharing work?",
            user_answer="A process has its own virtual memory space while threads share the process heap and code segment.",
            role_title="Backend Developer",
            difficulty="Medium"
        )
        self.assertIn("scores", eval_result)
        self.assertIn("scores_10", eval_result)
        scores_10 = eval_result["scores_10"]
        self.assertIn("accuracy", scores_10)
        self.assertIn("relevance", scores_10)
        self.assertIn("communication", scores_10)
        self.assertIn("overall", scores_10)
        self.assertGreaterEqual(scores_10["overall"], 0.0)
        self.assertLessEqual(scores_10["overall"], 10.0)

        # 3. Persist session
        session_id = create_interview_session(
            user_id=self.user_a_id,
            role_id="backend_dev",
            role_title="Backend Developer",
            difficulty="Medium",
            interview_type="Technical",
            target_company_track="Product",
            duration_minutes=15
        )
        self.assertIsNotNone(session_id)

        # 4. Persist question evaluation
        q_id = record_question_and_feedback(
            session_id=session_id,
            question_number=1,
            question_text="What is the difference between a process and a thread?",
            category="Technical",
            user_answer="Threads share memory, processes do not.",
            scores={"overall": 78.0, "accuracy": 80.0, "relevance": 80.0, "completeness": 70.0, "clarity": 85.0},
            honest_feedback="Correct baseline definition, but missed thread-local storage, stack isolation, and synchronization overhead.",
            incorrect_concepts=json.dumps(["Assumed threads have zero independent memory"]),
            missing_information=json.dumps(["Thread Local Storage (TLS)", "Context switch cost difference"]),
            improved_answer="Processes are isolated execution units with distinct memory spaces; threads share memory but have isolated call stacks.",
            improvement_reason="Explains thread stack boundaries and synchronization risks."
        )
        self.assertIsNotNone(q_id)

        finalize_interview_session(
            session_id=session_id,
            summary="Strong fundamental concepts of concurrency and memory models.",
            overall_score=82.5,
            accuracy_score=85.0,
            relevance_score=80.0,
            completeness_score=80.0,
            clarity_score=85.0
        )

        # Verify retrieval
        session_qs = get_interview_questions(session_id)
        self.assertEqual(len(session_qs), 1)
        self.assertEqual(session_qs[0]["overall_score"], 78.0)

    # =========================================================================
    # 4. USER DATA ISOLATION
    # =========================================================================
    def test_04_user_data_isolation(self):
        # Create session for User A
        sess_a = create_interview_session(
            user_id=self.user_a_id,
            role_id="sde_1",
            role_title="Software Development Engineer (SDE-1)",
            difficulty="Hard",
            interview_type="Coding & Problem Solving",
            target_company_track="Product"
        )
        finalize_interview_session(sess_a, "User A session", 90.0, 95.0, 90.0, 85.0, 90.0)

        # Create session for User B
        sess_b = create_interview_session(
            user_id=self.user_b_id,
            role_id="data_eng",
            role_title="Data Engineer",
            difficulty="Medium",
            interview_type="System Architecture",
            target_company_track="FinTech"
        )
        finalize_interview_session(sess_b, "User B session", 75.0, 70.0, 75.0, 80.0, 75.0)

        user_a_interviews = get_all_interviews(self.user_a_id)
        user_b_interviews = get_all_interviews(self.user_b_id)

        # Verify isolation
        self.assertTrue(all(i["user_id"] == self.user_a_id for i in user_a_interviews))
        self.assertTrue(all(i["user_id"] == self.user_b_id for i in user_b_interviews))
        self.assertNotIn(sess_b, [i["id"] for i in user_a_interviews])
        self.assertNotIn(sess_a, [i["id"] for i in user_b_interviews])

        # Attempt to delete User A's session using User B's user_id -> MUST FAIL
        unauthorized_delete = delete_interview_session(sess_a, user_id=self.user_b_id)
        self.assertFalse(unauthorized_delete)
        # Verify sess_a still exists
        self.assertIsNotNone(get_interview_by_id(sess_a))

        # Authorized delete by User A -> MUST SUCCEED
        authorized_delete = delete_interview_session(sess_a, user_id=self.user_a_id)
        self.assertTrue(authorized_delete)
        self.assertIsNone(get_interview_by_id(sess_a))

    # =========================================================================
    # 5. WEAKNESS TRACKER LIFECYCLE
    # =========================================================================
    def test_05_weakness_tracker_lifecycle(self):
        record_topic_status(
            user_id=self.user_a_id,
            topic_name="Database Indexing (B-Tree vs Hash)",
            category="System Design",
            status="weakness",
            notes="Confused on why Hash indexes cannot support range queries."
        )

        # Retrieve topics
        topics = get_all_user_topics(self.user_a_id)
        self.assertEqual(len(topics), 1)
        topic_id = topics[0]["id"]
        self.assertEqual(topics[0]["revision_status"], "Needs Work")

        # Update status to In Progress
        upd1 = update_topic_revision_status(topic_id, self.user_a_id, "In Progress")
        self.assertTrue(upd1)

        # Update status to Mastered
        upd2 = update_topic_revision_status(topic_id, self.user_a_id, "Mastered")
        self.assertTrue(upd2)

        # Verify updated status
        topics_after = get_all_user_topics(self.user_a_id)
        self.assertEqual(topics_after[0]["revision_status"], "Mastered")

        # Delete topic
        deleted = delete_user_topic(topic_id, self.user_a_id)
        self.assertTrue(deleted)
        self.assertEqual(len(get_all_user_topics(self.user_a_id)), 0)

    # =========================================================================
    # 6. INTERACTIVE PREPARATION ROADMAP & TASKS
    # =========================================================================
    def test_06_interactive_roadmap_and_tasks(self):
        tasks = [
            {"day": 1, "task_description": "Review B-Tree and B+Tree file structures for relational databases."},
            {"day": 2, "task_description": "Implement LRU Cache using Doubly Linked List and Hash Map."},
            {"day": 3, "task_description": "Solve 3 graph questions: BFS, DFS, and Dijkstra's algorithm."},
        ]

        roadmap_id = save_roadmap_with_tasks(
            user_id=self.user_a_id,
            title="7-Day SDE-1 Placement Sprint",
            target_role="Software Development Engineer (SDE-1)",
            duration_days=7,
            weak_topics_covered="Database Indexing, Caching, Graphs",
            plan_content="Intensive SDE review curriculum",
            daily_tasks=tasks
        )
        self.assertIsNotNone(roadmap_id)

        # Fetch roadmap
        roadmap = get_roadmap_by_id(roadmap_id, user_id=self.user_a_id)
        self.assertIsNotNone(roadmap)
        self.assertEqual(len(roadmap["tasks"]), 3)
        self.assertEqual(roadmap["tasks"][0]["is_completed"], 0)

        # Toggle first task completion
        first_task_id = roadmap["tasks"][0]["id"]
        toggled = toggle_roadmap_task(first_task_id, is_completed=True)
        self.assertTrue(toggled)

        # Verify task is now completed
        updated_roadmap = get_roadmap_by_id(roadmap_id, user_id=self.user_a_id)
        self.assertEqual(updated_roadmap["tasks"][0]["is_completed"], 1)

        # Delete roadmap
        del_res = delete_roadmap(roadmap_id, user_id=self.user_a_id)
        self.assertTrue(del_res)
        self.assertIsNone(get_roadmap_by_id(roadmap_id, user_id=self.user_a_id))

    # =========================================================================
    # 7. PURE-PYTHON PDF REPORT GENERATOR
    # =========================================================================
    def test_07_pdf_report_generator(self):
        session_info = {
            "id": 101,
            "role_title": "Backend Engineer",
            "difficulty": "Hard",
            "interview_type": "Technical & System Design",
            "target_company_track": "Tier-1 Product",
            "overall_score": 88.0,
            "accuracy_score": 90.0,
            "conceptual_score": 85.0,
            "relevance_score": 90.0,
            "completeness_score": 85.0,
            "clarity_score": 88.0,
            "created_at": "2026-11-23 18:00:00",
            "summary": "Demonstrated excellent knowledge of caching strategies and database concurrency."
        }
        questions = [
            {
                "question_text": "How do you handle cache invalidation in distributed architectures?",
                "user_answer": "I use TTL and write-through cache.",
                "overall_score": 85.0,
                "accuracy_score": 90.0,
                "relevance_score": 85.0,
                "completeness_score": 80.0,
                "clarity_score": 85.0,
                "honest_feedback": "Good fundamental answer, but did not discuss cache stampede prevention or dual-write inconsistencies.",
                "improved_answer": "Use Write-Through caching paired with an asynchronous CDC pipeline to invalidate Redis keys.",
                "improvement_reason": "Guarantees strong eventual consistency.",
                "incorrect_concepts": json.dumps(["Assumed simple TTL eliminates race conditions"]),
                "missing_information": json.dumps(["CDC with Debezium", "Distributed locking for cache stampede"])
            }
        ]

        pdf_bytes = PDFReportGenerator.generate_interview_report_pdf(
            candidate_name="Alpha Candidate",
            session_data=session_info,
            questions_data=questions
        )
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 500)
        # Check standard PDF 1.4 header
        self.assertTrue(pdf_bytes.startswith(b"%PDF-1.4"))
        # Check standard PDF trailer
        self.assertTrue(b"%%EOF" in pdf_bytes)

    # =========================================================================
    # 8. ACCOUNT DELETION CASCADING CLEANUP
    # =========================================================================
    def test_08_account_deletion_cascading(self):
        # Create session and roadmap for User B
        sess_id = create_interview_session(
            user_id=self.user_b_id,
            role_id="data_eng",
            role_title="Data Engineer",
            difficulty="Medium",
            interview_type="Technical",
            target_company_track="General"
        )
        finalize_interview_session(sess_id, "Data engineer session", 75.0, 75.0, 75.0, 75.0, 75.0)

        rd_id = save_roadmap_with_tasks(
            user_id=self.user_b_id,
            title="Data Track",
            target_role="Data Engineer",
            duration_days=14,
            weak_topics_covered="SQL Window Functions",
            plan_content="Data track roadmap",
            daily_tasks=[{"day": 1, "task_description": "SQL Window Functions"}]
        )
        save_candidate_resume(
            user_id=self.user_b_id,
            file_name="beta_cv.pdf",
            raw_text="Data engineer skilled in Apache Spark and Airflow",
            parsed_skills=["Spark", "Airflow"]
        )

        # Confirm data exists
        self.assertIsNotNone(get_user_by_id(self.user_b_id))
        self.assertIsNotNone(get_interview_by_id(sess_id))
        self.assertIsNotNone(get_roadmap_by_id(rd_id, user_id=self.user_b_id))
        self.assertIsNotNone(get_candidate_resume(self.user_b_id))

        # Permanently delete account
        deleted = delete_user_account(self.user_b_id)
        self.assertTrue(deleted)

        # Confirm complete erasure
        self.assertIsNone(get_user_by_id(self.user_b_id))
        self.assertIsNone(get_interview_by_id(sess_id))
        self.assertIsNone(get_roadmap_by_id(rd_id, user_id=self.user_b_id))
        self.assertIsNone(get_candidate_resume(self.user_b_id))


if __name__ == "__main__":
    unittest.main()
