"""
Unit tests for InterviewX UI Question Rendering, HTML Sanitization, and Responsiveness.
Verifies fixes for:
- Issue 1: Raw HTML display / markdown indentation bug
- Issue 2: Responsive layout and horizontal overflow prevention
- Issue 3: Clear distinction between Live AI Mode and Offline Heuristic Mode
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from components.cards import (
    sanitize_text,
    render_interview_question_card,
    render_evaluation_summary_card,
    render_honest_feedback_comparison
)
from services.gemini_service import GeminiService


class TestUIRenderingAndModeDistinction(unittest.TestCase):

    def test_01_sanitize_raw_html_questions(self):
        """Verify that questions with raw HTML tags are sanitized properly."""
        raw_html_q = '<h3 style="color: #0F172A;">How does a Hash Table handle collisions?</h3>'
        cleaned = sanitize_text(raw_html_q)
        self.assertEqual(cleaned, "How does a Hash Table handle collisions?")

        nested_html = '<div class="test"><p>Explain <b>TCP</b> vs <i>UDP</i></p></div>'
        self.assertEqual(sanitize_text(nested_html), "Explain TCP vs UDP")

        entity_html = "What is O(N &amp; log N) complexity in C++?"
        self.assertEqual(sanitize_text(entity_html), "What is O(N & log N) complexity in C++?")

        # Plain text should remain intact
        plain = "How does React Virtual DOM reconciliation work?"
        self.assertEqual(sanitize_text(plain), plain)

    def test_02_question_card_no_code_block_indentation(self):
        """Verify generated question card has zero 4+ space leading indentation lines."""
        # Test render_interview_question_card by inspecting markdown output
        import streamlit as st
        captured = []
        original_markdown = st.markdown

        def mock_markdown(content, unsafe_allow_html=False):
            captured.append(content)

        st.markdown = mock_markdown
        try:
            render_interview_question_card(
                question_text='<h3 style="color: #0F172A;">How does a Hash Table handle collisions?</h3>',
                category="Data Structures",
                question_number=1,
                total_questions=5,
                is_follow_up=False,
                is_offline=True,
                interviewer_intent="Assess internal hashing mechanics"
            )
            self.assertEqual(len(captured), 1)
            card_content = captured[0]

            # 1. No raw <h3> tags displayed as text
            self.assertNotIn('<h3 style="color: #0F172A;">', card_content)
            self.assertIn("How does a Hash Table handle collisions?", card_content)

            # 2. Check that no line begins with 4 or more spaces (the Markdown code block bug)
            lines = card_content.splitlines()
            for line in lines:
                if line.strip():
                    leading_spaces = len(line) - len(line.lstrip(" "))
                    self.assertLess(
                        leading_spaces, 4,
                        f"Line has >= 4 leading spaces which triggers Markdown <pre><code>: '{line}'"
                    )

            # 3. Check offline badge
            self.assertIn("Offline Question Bank", card_content)
        finally:
            st.markdown = original_markdown

    def test_03_ai_vs_offline_mode_distinction(self):
        """Verify that Live AI and Offline modes are explicitly and distinctly labeled."""
        import streamlit as st
        captured = []
        original_markdown = st.markdown

        def mock_markdown(content, unsafe_allow_html=False):
            captured.append(content)

        st.markdown = mock_markdown
        try:
            # 1. Offline Mode Card
            render_interview_question_card(
                question_text="What is a Process?",
                category="OS",
                question_number=1,
                total_questions=3,
                is_offline=True
            )
            self.assertIn("Offline Question Bank", captured[-1])
            self.assertNotIn("Live AI: Gemini", captured[-1])

            # 2. Live AI Mode Card
            render_interview_question_card(
                question_text="What is a Thread?",
                category="OS",
                question_number=2,
                total_questions=3,
                is_offline=False
            )
            self.assertIn("Live AI: Gemini 2.5 Flash", captured[-1])
            self.assertNotIn("Offline Question Bank", captured[-1])

            # 3. Evaluation Summary - Offline
            render_evaluation_summary_card(
                scores_100={"overall": 75.0, "accuracy": 70.0, "conceptual": 70.0, "clarity": 80.0, "relevance": 80.0},
                scores_10={"overall": 7.5, "accuracy": 7.0, "conceptual": 7.0, "communication": 8.0, "relevance": 8.0},
                is_offline=True
            )
            self.assertIn("Offline Heuristic Audit Engine", captured[-1])
            self.assertIn("Gemini API key is not active", captured[-1])

            # 4. Evaluation Summary - Live
            render_evaluation_summary_card(
                scores_100={"overall": 85.0, "accuracy": 90.0, "conceptual": 80.0, "clarity": 85.0, "relevance": 85.0},
                scores_10={"overall": 8.5, "accuracy": 9.0, "conceptual": 8.0, "communication": 8.5, "relevance": 8.5},
                is_offline=False
            )
            self.assertIn("Live AI Evaluation powered by", captured[-1])
            self.assertIn("Google Gemini 2.5 Flash", captured[-1])
        finally:
            st.markdown = original_markdown


if __name__ == "__main__":
    unittest.main()
