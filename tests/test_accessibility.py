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
        """Verify that app.py contains global skip link pointing to #main-content using semantic HTML without positive tabindex."""
        navbar_path = Path(__file__).resolve().parent.parent / "components" / "navbar.py"
        app_path = Path(__file__).resolve().parent.parent / "app.py"
        with open(navbar_path, "r", encoding="utf-8") as f:
            navbar_content = f.read()
        with open(app_path, "r", encoding="utf-8") as f:
            app_content = f.read()

        # Check skip link anchor attributes in app.py (rendered globally before sidebar and routing)
        self.assertIn('href="#main-content"', app_content)
        self.assertIn('class="skip-to-content"', app_content)
        self.assertIn('Skip to main content', app_content)
        self.assertIn('aria-label="Skip to main content"', app_content)

        # Ensure NO positive tabindex values are used (WCAG semantic compliance)
        self.assertNotIn('tabindex="1"', app_content)
        self.assertNotIn('tabindex="2"', app_content)
        self.assertNotIn('tabindex="1"', navbar_content)

        # Verify skip link is placed at top of main() before render_sidebar()
        skip_pos = app_content.find('class="skip-to-content"')
        sidebar_pos = app_content.find('render_sidebar()')
        self.assertNotEqual(skip_pos, -1, "Skip link must be present in app.py")
        self.assertNotEqual(sidebar_pos, -1, "Sidebar render call must be present in app.py")
        self.assertLess(skip_pos, sidebar_pos, "Skip link must be rendered before sidebar in app.py")

        # Verify exactly one global skip link exists across the app (no duplicate skip links)
        total_skip_links = navbar_content.count('class="skip-to-content"') + app_content.count('class="skip-to-content"')
        self.assertEqual(total_skip_links, 1, "There must be exactly one skip link globally to avoid duplicate skip links")

    def test_10_every_page_has_main_content_target(self):
        """Verify that every single page view assigns id='main-content' and tabindex='-1' to its primary heading."""
        base_dir = Path(__file__).resolve().parent.parent
        pages_to_check = [
            base_dir / "pages_modules" / "landing.py",
            base_dir / "components" / "auth_forms.py",
            base_dir / "pages_modules" / "dashboard.py",
            base_dir / "pages_modules" / "profile.py",
            base_dir / "pages_modules" / "interview.py",
            base_dir / "pages_modules" / "resume_analyzer.py",
            base_dir / "pages_modules" / "feedback.py",
            base_dir / "pages_modules" / "weakness_tracker.py",
            base_dir / "pages_modules" / "roadmap.py",
            base_dir / "pages_modules" / "analytics.py",
            base_dir / "pages_modules" / "history.py",
        ]

        for page_path in pages_to_check:
            with open(page_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn(
                'id="main-content"', content,
                f"Page {page_path.name} must contain an element with id='main-content'"
            )
            self.assertIn(
                'tabindex="-1"', content,
                f"Page {page_path.name} main-content target must have tabindex='-1' for programmatic focus"
            )

    def test_11_no_positive_tabindex_in_entire_codebase(self):
        """Verify that WCAG rule against positive tabindex values is strictly enforced across all application files."""
        base_dir = Path(__file__).resolve().parent.parent
        positive_tabindex_found = []
        for file_path in base_dir.rglob("*.py"):
            # Exclude tests directory, git, venv, and cache dirs
            if any(part in file_path.parts for part in [".git", "__pycache__", "venv", ".pytest_cache", "tests"]):
                continue
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            # Match tabindex="1" through "999" or tabindex='1'
            matches = re.findall(r'tabindex=[\'\"]\s*[1-9]\d*[\'\"]', content, re.IGNORECASE)
            if matches:
                positive_tabindex_found.append((str(file_path.relative_to(base_dir)), matches))

        self.assertEqual(
            positive_tabindex_found, [],
            f"Found positive tabindex values (WCAG violation): {positive_tabindex_found}"
        )


if __name__ == "__main__":
    unittest.main()
