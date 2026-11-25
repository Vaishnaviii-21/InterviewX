"""
Security, XSS Hardening, and Edge Case Verification Suite for InterviewX.
Tests password policy, XSS sanitization, resume file size limits, zip bomb defense,
and session authorization guards.
"""

import io
import zipfile
import html
import unittest
import streamlit as st
from auth.security import (
    validate_password,
    validate_username,
    validate_email,
    hash_password,
    verify_password
)
from auth.session_manager import render_auth_guard, init_session_state
from utils.resume_parser import ResumeParser, MAX_RESUME_BYTES, MAX_DECOMPRESSED_BYTES
from components.cards import sanitize_text

class TestSecurityAndEdgeCases(unittest.TestCase):
    """Verifies security controls, input validation, and denial-of-service protections."""

    def setUp(self):
        init_session_state()
        st.session_state["is_authenticated"] = False
        st.session_state["user"] = None

    def test_01_password_minimum_length_owasp_compliance(self):
        """Verify that validate_password strictly enforces the minimum 8-character OWASP standard."""
        # 1-7 chars must fail
        for length in range(1, 8):
            pwd = "A" * length
            valid, err = validate_password(pwd)
            self.assertFalse(valid, f"Password of length {length} must be rejected")
            self.assertIn("at least 8 characters", err)

        # Empty password
        valid, err = validate_password("")
        self.assertFalse(valid)
        self.assertIn("required", err)

        # 8 characters or more must succeed
        valid, err = validate_password("Pass1234")
        self.assertTrue(valid)
        self.assertEqual(err, "")

        # Passwords with leading or trailing whitespace must fail
        valid, err = validate_password("  Pass1234  ")
        self.assertFalse(valid)
        self.assertIn("whitespace", err)

    def test_02_password_hashing_and_timing_defense(self):
        """Verify PBKDF2 hashing format and constant-time verification."""
        pwd = "SecureStudentPass!9"
        hashed = hash_password(pwd)
        self.assertTrue(hashed.startswith("pbkdf2:sha256:100000$"))
        self.assertTrue(verify_password(pwd, hashed))
        self.assertFalse(verify_password("WrongPassword!9", hashed))
        self.assertFalse(verify_password("", hashed))
        self.assertFalse(verify_password(pwd, "invalid_hash_format"))

    def test_03_xss_injection_sanitization(self):
        """Verify that dangerous script and event handler payloads are stripped/escaped."""
        payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert(1)>",
            "<svg/onload=alert('document.cookie')>",
            "Candidate<script>steal()</script>Name",
            "<a href='javascript:evil()'>Click</a>"
        ]

        for payload in payloads:
            cleaned = sanitize_text(payload)
            self.assertNotIn("<script>", cleaned.lower())
            self.assertNotIn("onerror", cleaned.lower())
            self.assertNotIn("<img", cleaned.lower())
            self.assertNotIn("<svg", cleaned.lower())

            escaped = html.escape(payload)
            self.assertNotIn("<script>", escaped)
            self.assertIn("&lt;", escaped)

    def test_04_resume_parser_empty_and_zero_byte_safety(self):
        """Verify parser handles 0-byte or None inputs without crashing."""
        self.assertEqual(ResumeParser.extract_text_from_bytes(b"", "resume.pdf"), "")
        self.assertEqual(ResumeParser.extract_text_from_bytes(b"", "resume.docx"), "")
        self.assertEqual(ResumeParser.extract_text_from_bytes(b"", "resume.txt"), "")
        self.assertEqual(ResumeParser.extract_from_txt(b""), "")
        self.assertEqual(ResumeParser.extract_from_docx(b""), "")

    def test_05_resume_parser_oversized_file_rejection(self):
        """Verify that resumes exceeding MAX_RESUME_BYTES (5MB) are safely rejected."""
        oversized_bytes = b"0" * (MAX_RESUME_BYTES + 1024)
        result = ResumeParser.extract_text_from_bytes(oversized_bytes, "heavy_resume.pdf")
        self.assertEqual(result, "", "Files exceeding 5MB must be rejected")

    def test_06_docx_decompression_bomb_mitigation(self):
        """Verify that malicious DOCX files with giant uncompressed streams are safely rejected."""
        zip_buffer = io.BytesIO()
        valid_xml = b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:t>Safe text</w:t></w:p></w:body></w:document>'
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("word/document.xml", valid_xml)
        
        valid_bytes = zip_buffer.getvalue()
        # Verify valid docx extracts "Safe text"
        self.assertEqual(ResumeParser.extract_from_docx(valid_bytes), "Safe text")

        # Simulate a zip bomb where total uncompressed size exceeds limit
        class MockZipInfo:
            def __init__(self, filename, size):
                self.filename = filename
                self.file_size = size

        orig_zipfile = zipfile.ZipFile
        class BombZipFile(orig_zipfile):
            def infolist(self):
                return [MockZipInfo("word/document.xml", MAX_DECOMPRESSED_BYTES + 1024 * 1024)]

        zipfile.ZipFile = BombZipFile
        try:
            bomb_extracted = ResumeParser.extract_from_docx(valid_bytes)
            self.assertEqual(bomb_extracted, "", "DOCX exceeding uncompressed size cap must be rejected without decompression")
        finally:
            zipfile.ZipFile = orig_zipfile

    def test_07_auth_guard_behavior(self):
        """Verify that render_auth_guard protects views when unauthenticated and permits authenticated users."""
        captured_warnings = []
        original_warning = st.warning
        st.warning = lambda msg, icon=None: captured_warnings.append(msg)
        try:
            # 1. Unauthenticated test
            st.session_state["is_authenticated"] = False
            st.session_state["user"] = None
            guard_result = render_auth_guard("Secret Mock Results")
            self.assertFalse(guard_result)
            self.assertTrue(len(captured_warnings) > 0)
            self.assertIn("Secret Mock Results", captured_warnings[0])

            # 2. Authenticated test
            st.session_state["is_authenticated"] = True
            st.session_state["user"] = {"id": 1, "username": "testuser"}
            captured_warnings.clear()
            auth_guard_result = render_auth_guard("Secret Mock Results")
            self.assertTrue(auth_guard_result)
            self.assertEqual(len(captured_warnings), 0)
        finally:
            st.warning = original_warning


if __name__ == "__main__":
    unittest.main()
