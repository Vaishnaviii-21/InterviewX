"""
Unit and integration tests for skip-to-main-content accessibility across every page of InterviewX.
Verifies that:
1. The global skip-to-content link is rendered in app.py before sidebar or page routing.
2. Exactly one skip link exists globally without duplicates in the navbar or page views.
3. The link uses semantic HTML without positive tabindex.
4. Every single page (Home, Dashboard, Interview, Resume, Feedback, Weakness, Roadmap, Analytics, History, Profile, Auth)
   renders a unique #main-content target with tabindex='-1'.
5. Guard and active interview states preserve the #main-content anchor.
"""

import unittest
from pathlib import Path
import re

class TestSkipLinkEveryPage(unittest.TestCase):
    """Verifies skip link rendering, target presence, and tab navigation order on every page."""

    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parent.parent

    def test_global_skip_link_in_app(self):
        """Verify the global skip link is rendered in app.py before sidebar or page routing."""
        app_path = self.base_dir / "app.py"
        with open(app_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. Skip link exists
        self.assertIn('class="skip-to-content"', content)
        self.assertIn('href="#main-content"', content)
        self.assertIn('Skip to main content', content)
        self.assertIn('aria-label="Skip to main content"', content)

        # 2. Semantic HTML: NO positive tabindex
        self.assertNotIn('tabindex="1"', content)
        self.assertNotIn('tabindex="2"', content)
        self.assertNotIn("tabindex='1'", content)

        # 3. Execution order: Skip link must be before sidebar rendering in main()
        skip_idx = content.find('class="skip-to-content"')
        sidebar_idx = content.find('render_sidebar()')

        self.assertNotEqual(skip_idx, -1)
        self.assertNotEqual(sidebar_idx, -1)
        self.assertLess(skip_idx, sidebar_idx, "Skip link must precede render_sidebar() in app.py")

    def test_no_duplicate_skip_link_in_navbar(self):
        """Verify that components/navbar.py does not render a duplicate skip link."""
        navbar_path = self.base_dir / "components" / "navbar.py"
        with open(navbar_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertNotIn('class="skip-to-content"', content)
        self.assertNotIn('href="#main-content"', content)

    def test_exactly_one_skip_link_globally(self):
        """Verify that across the entire platform, exactly one skip link anchor is defined."""
        app_path = self.base_dir / "app.py"
        navbar_path = self.base_dir / "components" / "navbar.py"

        with open(app_path, "r", encoding="utf-8") as f:
            app_cnt = f.read().count('class="skip-to-content"')
        with open(navbar_path, "r", encoding="utf-8") as f:
            nav_cnt = f.read().count('class="skip-to-content"')

        total = app_cnt + nav_cnt
        self.assertEqual(total, 1, f"Expected exactly 1 global skip link, found {total}")

    def test_all_11_pages_have_main_content_target(self):
        """Verify each of the 11 pages assigns id='main-content' and tabindex='-1' to its primary heading."""
        pages = {
            "Home (Landing)": self.base_dir / "pages_modules" / "landing.py",
            "Candidate Dashboard": self.base_dir / "pages_modules" / "dashboard.py",
            "Resume Analyzer": self.base_dir / "pages_modules" / "resume_analyzer.py",
            "AI Mock Interview": self.base_dir / "pages_modules" / "interview.py",
            "Feedback Report": self.base_dir / "pages_modules" / "feedback.py",
            "Weakness Tracker": self.base_dir / "pages_modules" / "weakness_tracker.py",
            "Preparation Roadmap": self.base_dir / "pages_modules" / "roadmap.py",
            "Progress Analytics": self.base_dir / "pages_modules" / "analytics.py",
            "Interview History": self.base_dir / "pages_modules" / "history.py",
            "Candidate Profile": self.base_dir / "pages_modules" / "profile.py",
            "Auth Portal": self.base_dir / "components" / "auth_forms.py",
        }

        for page_name, page_path in pages.items():
            with self.subTest(page=page_name):
                with open(page_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Verify target exists
                self.assertIn('id="main-content"', content, f"{page_name} missing id='main-content'")
                # Verify tabindex="-1" exists for programmatic focus
                self.assertIn('tabindex="-1"', content, f"{page_name} missing tabindex='-1'")
                # Verify no positive tabindex on the page
                positive_tabindex = re.findall(r'tabindex=[\'\"]\s*[1-9]\d*[\'\"]', content)
                self.assertEqual(positive_tabindex, [], f"{page_name} contains forbidden positive tabindex: {positive_tabindex}")

    def test_auth_guard_has_main_content_target(self):
        """Verify that the unauthenticated access guard renders #main-content target."""
        guard_path = self.base_dir / "auth" / "session_manager.py"
        with open(guard_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('id="main-content"', content, "render_auth_guard must contain an element with id='main-content'")
        self.assertIn('tabindex="-1"', content, "render_auth_guard target must have tabindex='-1'")

    def test_styles_support_skip_link_and_main_content(self):
        """Verify CSS contains necessary positioning, transition, and scroll-margin rules."""
        css_path = self.base_dir / "static" / "styles.css"
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()

        # Skip link styling
        self.assertIn(".skip-to-content", css)
        self.assertIn("position: fixed;", css)
        self.assertIn("top: -120px;", css)
        self.assertIn(".skip-to-content:focus", css)
        self.assertIn("top: 0.75rem;", css)
        self.assertIn("opacity: 1;", css)
        self.assertIn("pointer-events: auto;", css)

        # Target styling
        self.assertIn("#main-content", css)
        self.assertIn("scroll-margin-top:", css)
        self.assertIn("scroll-behavior: smooth;", css)

if __name__ == "__main__":
    unittest.main()
