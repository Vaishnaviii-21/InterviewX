"""
Analytics service for InterviewX.
Processes raw database records to calculate interview metrics,
strengths/weaknesses distributions, and progress trends.
"""

from typing import Dict, Any, List
from database.models import get_user_analytics, get_all_interviews, get_user_by_id

class AnalyticsService:
    """Provides high-level metrics and structured data payloads for dashboard views."""

    @staticmethod
    def get_dashboard_summary(user_id: int = 1) -> Dict[str, Any]:
        """Fetches comprehensive analytics for the primary candidate dashboard."""
        analytics = get_user_analytics(user_id)
        user = get_user_by_id(user_id) or {
            "id": user_id,
            "name": "Candidate",
            "target_role": "Software Development Engineer (SDE-1)",
            "college": "Engineering Institute",
            "graduation_year": 2026
        }
        interviews = get_all_interviews(user_id, limit=5)

        # Readiness classification
        readiness_score = analytics.get("readiness_index", 0)
        if readiness_score >= 80:
            readiness_label = "Placement Ready"
            readiness_color = "#10B981"  # Emerald
            readiness_desc = "You are performing strongly across core CS and behavioral metrics."
        elif readiness_score >= 60:
            readiness_label = "Needs Target Polish"
            readiness_color = "#F59E0B"  # Amber
            readiness_desc = "Good conceptual baseline; focus on closing recurring weak points."
        else:
            readiness_label = "Early Prep Phase"
            readiness_color = "#EF4444"  # Rose
            readiness_desc = "Continue taking regular mocks to build technical depth and structure."

        # Latest interview score vs Previous for delta
        trends = analytics.get("score_trends", [])
        score_delta = None
        if len(trends) >= 2:
            score_delta = round(trends[-1]["overall_score"] - trends[-2]["overall_score"], 1)

        return {
            "user": user,
            "metrics": analytics,
            "readiness_label": readiness_label,
            "readiness_color": readiness_color,
            "readiness_desc": readiness_desc,
            "score_delta": score_delta,
            "recent_interviews": interviews
        }
