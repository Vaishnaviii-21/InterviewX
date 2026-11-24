"""
Unit & Integration Tests for InterviewX Logout, Login, and Data Preservation.
Validates:
1. Login flow and session state management.
2. Logout flow: session state clearing, active_page redirection to 'auth', and transient cache cleanup.
3. Data preservation on logout: user account, interviews, roadmaps, and topics remain intact in SQLite.
4. Re-login capability: users can log back in seamlessly with full access to their historical records.
5. Strict separation between Logout (preserves data) and Delete Account (permanently erases data).
6. Protected page gating: dashboard and tracking pages reject unauthenticated sessions.
"""

import sys
import json
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st
from database.connection import init_db, get_db_cursor
from database.models import (
    create_user,
    authenticate_user,
    get_user_by_id,
    delete_user_account,
    create_interview_session,
    record_question_and_feedback,
    finalize_interview_session,
    get_all_interviews,
    record_topic_status,
    get_all_user_topics,
    save_roadmap_with_tasks,
    get_user_roadmaps,
)
from auth.session_manager import (
    init_session_state,
    login_user,
    logout_user,
    get_current_user,
    is_authenticated,
)


class TestLogoutAndAuthentication(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        # Reset session state before each test
        init_session_state()
        st.session_state["is_authenticated"] = False
        st.session_state["user"] = None
        st.session_state["active_page"] = "landing"

        self.test_username = "logout_test_candidate"
        self.test_email = "logout_test@interviewx.ai"
        self.test_password = "SecurePassword@2026"

        # Clean up any leftover records
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("SELECT id FROM users WHERE username = ?", (self.test_username,))
            row = cursor.fetchone()
            if row:
                delete_user_account(row["id"])

        user, err = create_user(
            username=self.test_username,
            email=self.test_email,
            password=self.test_password,
            name="Logout Candidate",
            college="BITS Pilani",
            degree="B.Tech Computer Science",
            graduation_year=2026,
            target_role="Software Development Engineer (SDE-1)",
            target_company_track="Product / Tier-1 Tech (FAANG/MAANG)"
        )
        self.assertIsNotNone(user, f"Failed to create test user: {err}")
        self.user_id = user["id"]

    def tearDown(self):
        if hasattr(self, "user_id") and self.user_id:
            delete_user_account(self.user_id)
        # Clear session state
        st.session_state["is_authenticated"] = False
        st.session_state["user"] = None

    def test_01_login_flow(self):
        """Test successful authentication and login_user session state setup."""
        auth_user, err = authenticate_user(self.test_username, self.test_password)
        self.assertIsNotNone(auth_user)
        self.assertEqual(err, "")

        login_user(auth_user)

        self.assertTrue(is_authenticated())
        current = get_current_user()
        self.assertIsNotNone(current)
        self.assertEqual(current["id"], self.user_id)
        self.assertEqual(current["username"], self.test_username)
        self.assertNotIn("password_hash", current)

    def test_02_logout_flow_and_session_clearing(self):
        """Test that logout_user clears session, redirects to 'auth', and clears caches."""
        auth_user, _ = authenticate_user(self.test_username, self.test_password)
        login_user(auth_user)
        self.assertTrue(is_authenticated())

        # Set up transient mock session state
        st.session_state["active_interview"] = {"in_progress": True, "question_index": 2}
        st.session_state["view_session_id"] = 42
        st.session_state["use_resume_mode"] = True
        st.session_state["active_roadmap_id"] = 7
        st.session_state["active_page"] = "dashboard"

        # Execute Logout
        logout_user()

        # Verify authentication state is cleared
        self.assertFalse(is_authenticated())
        self.assertIsNone(get_current_user())
        self.assertIsNone(st.session_state.get("user"))
        self.assertFalse(st.session_state.get("is_authenticated"))

        # Verify redirection to Login page
        self.assertEqual(st.session_state.get("active_page"), "auth")

        # Verify transient caches are cleaned up
        self.assertNotIn("active_interview", st.session_state)
        self.assertNotIn("view_session_id", st.session_state)
        self.assertFalse(st.session_state.get("use_resume_mode", False))
        self.assertNotIn("active_roadmap_id", st.session_state)

    def test_03_logout_preserves_database_data(self):
        """Verify that logging out does NOT delete user account, interviews, topics, or roadmaps."""
        # 1. Create interview session and record question
        sess_id = create_interview_session(
            user_id=self.user_id,
            role_id="sde_1",
            role_title="Software Development Engineer",
            difficulty="Medium",
            interview_type="Technical",
            target_company_track="Product",
            duration_minutes=20
        )
        record_question_and_feedback(
            session_id=sess_id,
            question_number=1,
            question_text="Explain Database Indexing (B-Tree).",
            category="Databases",
            user_answer="B-trees keep data sorted and allow logarithmic searches.",
            scores={"overall": 85.0, "accuracy": 85.0},
            honest_feedback="Good explanation.",
            incorrect_concepts="[]",
            missing_information="[]",
            improved_answer="B-Tree indexes maintain sorted balanced tree structures.",
            improvement_reason="Comprehensive indexing detail."
        )
        finalize_interview_session(
            session_id=sess_id,
            summary="Solid performance.",
            overall_score=85.0,
            accuracy_score=85.0,
            relevance_score=85.0,
            completeness_score=80.0,
            clarity_score=85.0
        )

        # 2. Add topic / weakness
        record_topic_status(
            user_id=self.user_id,
            topic_name="Database Normalization",
            category="Databases",
            status="weakness",
            notes="Review 3NF vs BCNF"
        )

        # 3. Create roadmap
        save_roadmap_with_tasks(
            user_id=self.user_id,
            title="SDE-1 14-Day Plan",
            target_role="Software Development Engineer",
            duration_days=14,
            weak_topics_covered="B-Trees, Indexing",
            plan_content="14-day study plan covering DB structures.",
            daily_tasks=[{"day": 1, "topic": "B-Trees", "description": "Study balanced trees", "is_completed": 0}]
        )

        # 4. Log in and then log out
        auth_user, _ = authenticate_user(self.test_username, self.test_password)
        login_user(auth_user)
        self.assertTrue(is_authenticated())

        logout_user()
        self.assertFalse(is_authenticated())

        # 5. Verify database records are 100% preserved
        db_user = get_user_by_id(self.user_id)
        self.assertIsNotNone(db_user, "User account was accidentally deleted on logout!")
        self.assertEqual(db_user["username"], self.test_username)

        interviews = get_all_interviews(self.user_id)
        self.assertEqual(len(interviews), 1, "Interview records were lost on logout!")
        self.assertEqual(interviews[0]["id"], sess_id)

        topics = get_all_user_topics(self.user_id)
        self.assertEqual(len(topics), 1, "User topics were lost on logout!")
        self.assertEqual(topics[0]["topic_name"], "Database Normalization")

        roadmaps = get_user_roadmaps(self.user_id)
        self.assertEqual(len(roadmaps), 1, "User roadmaps were lost on logout!")

        # 6. Verify user can log back in seamlessly with same credentials
        reauth_user, err = authenticate_user(self.test_username, self.test_password)
        self.assertIsNotNone(reauth_user, f"Re-login failed after logout: {err}")
        login_user(reauth_user)
        self.assertTrue(is_authenticated())
        self.assertEqual(get_current_user()["id"], self.user_id)

    def test_04_delete_account_vs_logout_separation(self):
        """Verify that Delete Account deletes SQLite data, whereas Logout strictly preserves it."""
        # Log out should preserve
        auth_user, _ = authenticate_user(self.test_username, self.test_password)
        login_user(auth_user)
        logout_user()
        self.assertIsNotNone(get_user_by_id(self.user_id))

        # Delete Account should permanently remove user
        deleted = delete_user_account(self.user_id)
        self.assertTrue(deleted)
        self.assertIsNone(get_user_by_id(self.user_id), "User still exists after delete_user_account!")

    def test_05_protected_pages_block_unauthenticated_access(self):
        """Verify that protected dashboard pages display security guards when unauthenticated."""
        from pages_modules.dashboard import render_dashboard
        from pages_modules.analytics import render_analytics_page
        from pages_modules.history import render_history_page
        from pages_modules.weakness_tracker import render_weakness_tracker_page
        from pages_modules.roadmap import render_roadmap_page
        from pages_modules.profile import render_profile_page

        # Ensure session is logged out
        logout_user()
        self.assertFalse(is_authenticated())

        captured_warnings = []
        original_warning = st.warning
        original_info = st.info

        def mock_warning(msg, icon=None):
            captured_warnings.append(msg)

        def mock_info(msg, icon=None):
            captured_warnings.append(msg)

        st.warning = mock_warning
        st.info = mock_info
        try:
            # 1. Candidate Dashboard
            render_dashboard()
            self.assertTrue(any("Protected Page" in w or "signed in" in w for w in captured_warnings))

            # 2. Progress Analytics
            captured_warnings.clear()
            render_analytics_page()
            self.assertTrue(any("Protected Page" in w or "signed in" in w for w in captured_warnings))

            # 3. History
            captured_warnings.clear()
            render_history_page()
            self.assertTrue(any("Protected Page" in w or "signed in" in w for w in captured_warnings))

            # 4. Weakness Tracker
            captured_warnings.clear()
            render_weakness_tracker_page()
            self.assertTrue(any("Protected Page" in w or "signed in" in w for w in captured_warnings))

            # 5. Roadmap
            captured_warnings.clear()
            render_roadmap_page()
            self.assertTrue(any("Protected Page" in w or "signed in" in w for w in captured_warnings))

            # 6. Profile
            captured_warnings.clear()
            render_profile_page()
            self.assertTrue(any("sign in" in w.lower() for w in captured_warnings))
        finally:
            st.warning = original_warning
            st.info = original_info


if __name__ == "__main__":
    unittest.main()
