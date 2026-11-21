from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from backend.models.schemas import RecommendationItem


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


def generate_recommendations(
    score_results: Dict[str, Any],
    skill_validation_results: Dict[str, Any],
    jd_comparison: Optional[Dict[str, Any]] = None,
) -> List[RecommendationItem]:
    """Generate prioritized actionable recommendations with impact potential."""
    recs: List[RecommendationItem] = []

    # 1. Skill Validation Recommendation
    unvalidated = skill_validation_results.get("unvalidated_skills", [])
    val_pct = skill_validation_results.get("validation_percentage", 0.0)
    if unvalidated:
        priority = "critical" if val_pct < 0.4 else "high" if val_pct < 0.7 else "medium"
        impact = 8.0 if val_pct < 0.4 else 5.0
        actions = [
            f"Add project context or bullet point demonstrating practical usage of '{s}'"
            for s in unvalidated[:4]
        ]
        if len(unvalidated) > 4:
            actions.append(f"...and validate {len(unvalidated) - 4} other skills or remove them.")
        recs.append(
            RecommendationItem(
                title="Corroborate Claimed Skills in Projects",
                description=f"{len(unvalidated)} listed skills have no evidence in your projects or work history.",
                priority=priority,
                impact_score=impact,
                category="skill_validation",
                action_items=actions,
            )
        )

    # 2. Keyword & JD Alignment
    if jd_comparison:
        missing_kw = jd_comparison.get("missing_keywords", [])
        match_pct = jd_comparison.get("match_percentage", 0.0)
        if missing_kw and match_pct < 75.0:
            recs.append(
                RecommendationItem(
                    title="Integrate Target Job Keywords",
                    description=f"Your resume matches {match_pct:.0f}% of target role criteria. Closing keyword gaps will directly increase ATS match rank.",
                    priority="high" if match_pct < 60.0 else "medium",
                    impact_score=7.5,
                    category="keywords",
                    action_items=[f"Incorporate '{kw}' organically into summary, skills, or bullet points" for kw in missing_kw[:5]],
                )
            )

    # 3. Content Metrics Recommendation
    content_score = score_results.get("content_score", 0.0)
    if content_score < 18.0:
        recs.append(
            RecommendationItem(
                title="Add Quantifiable Metrics to Achievements",
                description="Hiring algorithms and screening managers look for numbers, percentages, and scale metrics.",
                priority="high",
                impact_score=6.0,
                category="content",
                action_items=[
                    "Quantify your accomplishments (e.g. 'boosted throughput by 30%', 'saved $15K annually').",
                    "Specify team sizes, daily active user counts, or code test coverage figures.",
                ],
            )
        )

    # 4. Formatting Recommendation
    fmt_score = score_results.get("formatting_score", 0.0)
    if fmt_score < 15.0:
        recs.append(
            RecommendationItem(
                title="Improve Section Structure and Bullet Formatting",
                description="Ensure clear headings (Summary, Experience, Projects, Education, Skills) with uniform bullet points.",
                priority="medium",
                impact_score=5.0,
                category="formatting",
                action_items=[
                    "Use standard single-column reverse-chronological layout.",
                    "Ensure every experience item contains Job Title, Company, Location, and Date.",
                ],
            )
        )

    return recs
