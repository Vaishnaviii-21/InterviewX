"""
Accessibility & WCAG Verification Test Suite for InterviewX.
Verifies semantic headings, keyboard focus accessibility, WCAG contrast compliance,
screen reader utilities, and ARIA labels.
"""

import re
import unittest
from pathlib import Path
from components.cards import (
    render_metric_card,
    render_interview_question_card,
    render_honest_feedback_comparison
)

def hex_to_relative_luminance(hex_str: str) -> float:
    """Calculates WCAG 2.1 relative luminance for a 6-digit hex color."""
    hex_clean = hex_str.strip().lstrip("#")
    r = int(hex_clean[0:2], 16) / 255.0
    g = int(hex_clean[2:4], 16) / 255.0
    b = int(hex_clean[4:6], 16) / 255.0

    def to_linear(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * to_linear(r) + 0.7152 * to_linear(g) + 0.0722 * to_linear(b)

def contrast_ratio_against_white(hex_str: str) -> float:
    """Calculates WCAG contrast ratio of a text color against white background (#FFFFFF)."""
    lum_text = hex_to_relative_luminance(hex_str)
    lum_white = 1.0
    return (lum_white + 0.05) / (lum_text + 0.05)

class TestAccessibility(unittest.TestCase):
    """Verifies accessibility rules and WCAG AA/AAA compliance across InterviewX."""

    @classmethod
    def setUpClass(cls):
        cls.css_path = Path(__file__).resolve().parent.parent / "static" / "styles.css"
        with open(cls.css_path, "r", encoding="utf-8") as f:
            cls.css_content = f.read()

    def test_01_text_muted_contrast_meets_wcag_aa(self):
        """Verify that --text-muted in styles.css satisfies WCAG AA >= 4.5:1 on white."""
        match = re.search(r"--text-muted:\s*(#[0-9a-fA-F]{6})", self.css_content)
        self.assertIsNotNone(match, "--text-muted custom property must be defined in styles.css")
        muted_hex = match.group(1)
        ratio = contrast_ratio_against_white(muted_hex)
        # WCAG AA requires >= 4.5:1 for normal body text
        self.assertGreaterEqual(
            ratio, 4.5,
            f"--text-muted ({muted_hex}) contrast ratio against white is {ratio:.2f}:1, below WCAG AA 4.5:1"
        )

    def test_02_focus_visible_styling_present(self):
        """Verify that :focus-visible rules exist for keyboard accessibility."""
        self.assertIn(":focus-visible", self.css_content)
        self.assertIn("outline:", self.css_content)

    def test_03_screen_reader_utilities_present(self):
        """Verify that .sr-only and reduced-motion media queries exist."""
        self.assertIn(".sr-only", self.css_content)
        self.assertIn("prefers-reduced-motion", self.css_content)
        self.assertIn("clip: rect(0, 0, 0, 0)", self.css_content)

    def test_04_skip_to_content_styling_present(self):
        """Verify that .skip-to-content navigation bypass and #main-content exist with proper styling in styles.css."""
        self.assertIn(".skip-to-content", self.css_content)
        self.assertIn(".skip-to-content:focus", self.css_content)
        self.assertIn("#main-content", self.css_content)
        self.assertIn("scroll-margin-top:", self.css_content)
        self.assertIn("scroll-behavior: smooth", self.css_content)

    def test_05_metric_cards_contain_accessible_attributes(self):
        """Verify that metric cards use role='region', aria-label, and screen reader text."""
        import streamlit as st
        captured = []
        orig_markdown = st.markdown
        st.markdown = lambda content, unsafe_allow_html=False: captured.append(content)
        try:
            render_metric_card(
                label="Overall Readiness",
                value="82%",
                delta="+5%",
                delta_positive=True
            )
            self.assertTrue(len(captured) > 0)
            html = captured[0]
            self.assertIn('role="region"', html)
            self.assertIn('aria-label="Overall Readiness metric"', html)
            self.assertIn('class="sr-only"', html)
            self.assertIn('Increased by', html)
        finally:
            st.markdown = orig_markdown

    def test_06_interview_question_card_uses_semantic_headings(self):
        """Verify that question card renders semantic <h3> and aria attributes."""
        import streamlit as st
        captured = []
        orig_markdown = st.markdown
        st.markdown = lambda content, unsafe_allow_html=False: captured.append(content)
        try:
            render_interview_question_card(
                question_text="Explain how hash collisions are resolved.",
                category="Data Structures",
                question_number=1,
                total_questions=5,
                interviewer_intent="Collision resolution mechanisms"
            )
            self.assertTrue(len(captured) > 0)
            html = captured[0]
            self.assertIn('role="region"', html)
            self.assertIn('aria-label="Interview Question Card: Question 1 of 5"', html)
            self.assertIn('<h3 class="interview-question-title">', html)
            self.assertIn('Explain how hash collisions are resolved.', html)
        finally:
            st.markdown = orig_markdown

    def test_07_feedback_sections_use_semantic_headings(self):
        """Verify that honest feedback card renders semantic <h4> and <h5> tags."""
        import streamlit as st
        captured = []
        orig_markdown = st.markdown
        st.markdown = lambda content, unsafe_allow_html=False: captured.append(content)
        try:
            render_honest_feedback_comparison(
                question="Explain how hash collisions are resolved.",
                user_answer="You use linear probing only.",
                honest_critique="Good start, but misses chaining.",
                incorrect_concepts=["Equated open addressing with hash table standard"],
                missing_info=["Separate chaining via linked list or red-black trees"],
                improved_answer="Hash collisions can be handled using separate chaining or open addressing.",
                why_better="More comprehensive and mentions Big-O tradeoffs."
            )
            self.assertTrue(len(captured) > 0)
            html = captured[0]
            self.assertIn('role="region"', html)
            self.assertIn('aria-label="Feedback and Benchmark Analysis"', html)
            self.assertIn('<h4', html)
            self.assertIn('<h5', html)
            self.assertIn('Equated open addressing with hash table standard', html)
        finally:
            st.markdown = orig_markdown

    def test_08_page_title_h1_defined_in_styles(self):
        """Verify that .page-title-h1 styling is present in styles.css."""
        self.assertIn(".page-title-h1", self.css_content)

    def test_09_skip_link_markup_and_anchor_target_in_app(self):
        """Verify that app.py contains skip link pointing to #main-content and matching unique anchor container."""
        app_path = Path(__file__).resolve().parent.parent / "app.py"
        with open(app_path, "r", encoding="utf-8") as f:
            app_content = f.read()

        # Check skip link anchor
        self.assertIn('href="#main-content"', app_content)
        self.assertIn('class="skip-to-content"', app_content)
        self.assertIn('Skip to main content', app_content)

        # Check unique main content target container with tabindex="-1"
        self.assertIn('id="main-content"', app_content)
        self.assertIn('tabindex="-1"', app_content)
        self.assertIn('main-content-target', app_content)


if __name__ == "__main__":
    unittest.main()
