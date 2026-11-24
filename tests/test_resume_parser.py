import sys
import io
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.resume_parser import ResumeParser, ResumeAnalyzer

def test_resume_parser():
    print("--- TESTING RESUME PARSER & ANALYZER ---")

    # 1. Test TXT parsing
    sample_resume_txt = """
    Rohan Sharma
    Email: rohan.sharma@example.com | Phone: +91 9876543210
    Education: B.Tech in Computer Science and Engineering, National Institute of Technology, 2026, CGPA: 8.4
    
    Technical Skills:
    - Languages: Python, Java, C++, SQL, JavaScript
    - Frameworks & Libraries: React, Node.js, FastAPI, Django, Pandas, NumPy
    - Databases: PostgreSQL, MongoDB, Redis
    - Tools: Git, Docker, Linux, Postman
    
    Projects:
    1. Distributed Task Queue
       Built a background worker task queue with Python and Redis for asynchronous email processing.
    2. Campus Placement Portal
       Developed a full-stack platform using React, FastAPI, and PostgreSQL with JWT authentication.
    
    Experience:
    Software Engineering Intern at FinTech Startup (Jan 2025 - June 2025)
    - Designed REST APIs for payments gateway integration.
    """

    txt_bytes = sample_resume_txt.encode("utf-8")
    extracted_txt = ResumeParser.extract_text_from_bytes(txt_bytes, "rohan_resume.txt")
    assert len(extracted_txt) > 100, "TXT text extraction failed"
    print("✔ TXT text extraction passed.")

    # 2. Test DOCX parsing with in-memory zip
    docx_buffer = io.BytesIO()
    with zipfile.ZipFile(docx_buffer, "w") as zf:
        xml_doc = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p><w:r><w:t>Aakash Gupta - Software Engineer</w:t></w:r></w:p>
                <w:p><w:r><w:t>B.Tech Computer Science 2026. Proficient in Python, React, and SQL.</w:t></w:r></w:p>
                <w:p><w:r><w:t>Projects: AI Recommendation Engine using PyTorch and FastAPI.</w:t></w:r></w:p>
            </w:body>
        </w:document>"""
        zf.writestr("word/document.xml", xml_doc)

    docx_bytes = docx_buffer.getvalue()
    extracted_docx = ResumeParser.extract_text_from_bytes(docx_bytes, "aakash_resume.docx")
    assert "Aakash Gupta" in extracted_docx, f"DOCX text extraction failed: {extracted_docx}"
    assert "Python" in extracted_docx, "DOCX content missing"
    print("✔ Pure-Python DOCX text extraction passed.")

    # 3. Test Resume Analyzer
    analysis = ResumeAnalyzer.analyze_resume(extracted_txt, "rohan_resume.txt")
    assert "Python" in analysis["parsed_skills"], "Python skill missing from analysis"
    assert "React.js" in analysis["parsed_skills"] or "React" in analysis["parsed_skills"], "React skill missing"
    assert "PostgreSQL" in analysis["parsed_skills"], "PostgreSQL skill missing"
    assert len(analysis["parsed_projects"]) >= 1, "Projects not extracted"
    assert len(analysis["parsed_education"]) >= 1, "Education not extracted"
    assert len(analysis["missing_skills"]) >= 1, "Missing skills list empty"
    assert len(analysis["interview_questions"]) >= 3, "Interview questions not generated"
    assert analysis["summary"] != "", "Summary empty"
    print(f"✔ Resume Analysis passed. Extracted {len(analysis['parsed_skills'])} skills, {len(analysis['interview_questions'])} questions.")

    print("🎉 ALL RESUME PARSER TESTS PASSED!")

if __name__ == "__main__":
    test_resume_parser()
