import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.pdf_generator import PDFReportGenerator

def test_pdf():
    session_data = {
        "role_title": "Python Developer",
        "difficulty": "Intermediate",
        "interview_type": "Technical Interview",
        "created_at": "2026-11-23 18:00:00",
        "overall_score": 82.5,
        "accuracy_score": 85.0,
        "conceptual_score": 80.0,
        "relevance_score": 85.0,
        "clarity_score": 80.0,
        "readiness_assessment": "Placement Ready",
        "summary": "Demonstrated solid Python runtime and web framework knowledge."
    }
    questions_data = [
        {
            "question_number": 1,
            "question_text": "Explain Python GIL and multithreading behavior.",
            "category": "Python Internals",
            "user_answer": "GIL allows only one thread to execute Python bytecode at a time.",
            "overall_score": 85.0,
            "honest_feedback": "Accurate explanation of the mutex lock. Good mention of CPU vs IO bound trade-offs.",
            "improved_answer": "In CPython, the Global Interpreter Lock (GIL) is a mutual exclusion lock..."
        }
    ]

    pdf_bytes = PDFReportGenerator.generate_interview_report_pdf("Arjun Verma", session_data, questions_data)
    assert pdf_bytes.startswith(b"%PDF-1.4"), "Invalid PDF header"
    assert b"%%EOF" in pdf_bytes, "Missing PDF EOF"
    assert len(pdf_bytes) > 500, "PDF suspiciously small"
    print(f"✔ PDF generated successfully ({len(pdf_bytes)} bytes).")

if __name__ == "__main__":
    test_pdf()
