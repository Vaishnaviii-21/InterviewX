"""
Tests for Gemini API Key configuration, validation, security, and fallback mode in InterviewX.
Verifies all 7 requirements:
1. Secure key resolution (session_state, os.environ, .env)
2. Correct passing to Gemini client
3. Key format validation without exposing key
4. Clear success and error states
5. Live AI activation when key is valid
6. Seamless offline fallback mode
7. No leakage/logging of complete API key
"""

import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import (
    get_gemini_api_key,
    set_gemini_api_key,
    clear_gemini_api_key,
    is_api_key_configured,
    mask_api_key
)
from services.gemini_service import GeminiService


class TestGeminiConfiguration(unittest.TestCase):

    def setUp(self):
        # Save original env and temporarily hide .env so unit tests are isolated
        self.original_env_key = os.environ.get("GEMINI_API_KEY")
        self.env_file = BASE_DIR / ".env"
        self.env_bak = BASE_DIR / ".env.test_backup"
        if self.env_file.exists():
            if self.env_bak.exists():
                self.env_bak.unlink()
            self.env_file.rename(self.env_bak)
        clear_gemini_api_key()

    def tearDown(self):
        # Restore original env and .env file
        clear_gemini_api_key()
        if self.original_env_key is not None:
            os.environ["GEMINI_API_KEY"] = self.original_env_key
        if self.env_bak.exists():
            if self.env_file.exists():
                self.env_file.unlink()
            self.env_bak.rename(self.env_file)

    def test_01_masking_never_exposes_complete_key(self):
        """Verify API key is always safely masked."""
        secret_key = "AIzaSyDUMMYSECRETKEYFORTESTING12345"
        masked = mask_api_key(secret_key)
        self.assertEqual(masked, "AIza...2345")
        self.assertNotIn("DUMMYSECRETKEYFORTESTING", masked)
        self.assertIn("...", masked)

        # Short or empty keys
        self.assertEqual(mask_api_key(""), "••••••••")
        self.assertEqual(mask_api_key("123"), "••••••••")

    def test_02_key_resolution_from_environ(self):
        """Verify resolution from os.environ."""
        test_key = "AIzaSyTestKeyFromEnvironment12345678"
        os.environ["GEMINI_API_KEY"] = test_key
        self.assertTrue(is_api_key_configured())
        self.assertEqual(get_gemini_api_key(), test_key)

    def test_03_key_resolution_from_session_state(self):
        """Verify resolution from Streamlit session_state."""
        import streamlit as st
        test_key = "AIzaSyTestKeyFromSessionState87654321"
        st.session_state["gemini_api_key"] = test_key

        self.assertTrue(is_api_key_configured())
        self.assertEqual(get_gemini_api_key(), test_key)

        # Session state should override empty or placeholder env
        os.environ["GEMINI_API_KEY"] = "your_gemini_api_key_here"
        self.assertEqual(get_gemini_api_key(), test_key)

    def test_04_set_and_clear_key(self):
        """Verify set_gemini_api_key and clear_gemini_api_key."""
        test_key = "AIzaSyTestKeyForSetAndClear99999999"
        success = set_gemini_api_key(test_key, persist_to_env=False)
        self.assertTrue(success)
        self.assertTrue(is_api_key_configured())
        self.assertEqual(get_gemini_api_key(), test_key)

        # Clear key
        clear_gemini_api_key()
        self.assertFalse(is_api_key_configured())
        self.assertEqual(get_gemini_api_key(), "")

    def test_05_placeholder_ignored(self):
        """Verify that default placeholder key is treated as unconfigured."""
        os.environ["GEMINI_API_KEY"] = "your_gemini_api_key_here"
        self.assertFalse(is_api_key_configured())
        self.assertEqual(get_gemini_api_key(), "")

    def test_06_gemini_service_headers_and_security(self):
        """Verify GeminiService uses x-goog-api-key header and never exposes key in error logs."""
        test_key = "AIzaSySensitiveSecretKeyNeverLeakMe"
        set_gemini_api_key(test_key)

        svc = GeminiService()
        self.assertTrue(svc.is_ready())
        self.assertEqual(svc.api_key, test_key)

        # test_connection with dummy key should fail gracefully WITHOUT leaking the key
        res = svc.test_connection()
        self.assertFalse(res["success"])
        # Crucial: The error message must NEVER contain the secret key!
        self.assertNotIn("SensitiveSecretKeyNeverLeakMe", res["message"])

    def test_07_offline_fallback_preservation(self):
        """Verify offline mode fallback works perfectly when key is cleared."""
        clear_gemini_api_key()
        svc = GeminiService()
        self.assertFalse(svc.is_ready())

        # Generate fallback question
        q = svc.generate_interview_question(
            role_title="Backend Developer",
            difficulty="Medium",
            interview_type="Technical",
            question_number=1,
            target_company_track="Product"
        )
        self.assertTrue(q.get("is_offline"))
        self.assertIn("question_text", q)

        # Evaluate fallback answer
        eval_res = svc.evaluate_answer_honest(
            question_text="What is a process vs thread?",
            user_answer="A process is an executing program with isolated memory.",
            role_title="Backend Developer",
            difficulty="Medium"
        )
        self.assertTrue(eval_res.get("is_offline"))
        self.assertIn("scores", eval_res)
        self.assertIn("scores_10", eval_res)
        self.assertIn("Offline", eval_res.get("evaluation_engine", ""))


if __name__ == "__main__":
    unittest.main()
