import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger("ats_resume_scorer")

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


def format_date(value: Any, fmt: str = "%B %d, %Y at %I:%M %p") -> str:
    """Format ISO date string to human-readable format."""
    if not value:
        return datetime.now().strftime(fmt)
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.strftime(fmt)
    except Exception:
        return str(value)


env.filters["format_date"] = format_date


def generate_html_reports(analysis_data: Dict[str, Any]) -> Dict[str, str]:
    """Render HTML templates for PDF generation."""
    overall_score = float(analysis_data.get("ATS_score", analysis_data.get("ats_score", 0.0)))
    interpretation = analysis_data.get("interpretation", "")
    cs = analysis_data.get("component_scores", {})
    if hasattr(cs, "__dict__"):
        cs = cs.__dict__

    component_scores = {
        "formatting": float(cs.get("formatting", 0)),
        "keywords": float(cs.get("keywords", 0)),
        "content": float(cs.get("content", 0)),
        "skill_validation": float(cs.get("skill_validation", 0)),
        "ats_compatibility": float(cs.get("ats_compatibility", 0)),
    }

    def pct(score, max_score):
        return min(100, max(0, round(score / max_score * 100)))

    component_pct = {
        "formatting": pct(component_scores["formatting"], 20),
        "keywords": pct(component_scores["keywords"], 25),
        "content": pct(component_scores["content"], 25),
        "skill_validation": pct(component_scores["skill_validation"], 15),
        "ats_compatibility": pct(component_scores["ats_compatibility"], 15),
    }

    raw_feedback = analysis_data.get("detailed_feedback", [])

    def to_dict(item):
        if isinstance(item, dict):
            return item
        return item.model_dump() if hasattr(item, "model_dump") else item.__dict__

    detailed_feedback = [to_dict(fb) for fb in raw_feedback]

    high_priority = [fb for fb in detailed_feedback if fb.get("severity_level", "").lower() in ("high", "critical")]
    medium_priority = [fb for fb in detailed_feedback if fb.get("severity_level", "").lower() in ("moderate", "medium")]
    low_priority = [fb for fb in detailed_feedback if fb.get("severity_level", "").lower() in ("low", "info")]

    score_color = "#16a34a" if overall_score >= 80 else "#d97706" if overall_score >= 60 else "#dc2626"

    context = {
        "overall_score": overall_score,
        "score_color": score_color,
        "interpretation": interpretation,
        "component_scores": component_scores,
        "component_pct": component_pct,
        "strengths": analysis_data.get("strengths", []),
        "critical_issues": analysis_data.get("critical_issues", []),
        "detailed_feedback": detailed_feedback,
        "high_priority": high_priority,
        "medium_priority": medium_priority,
        "low_priority": low_priority,
        "skill_validation": analysis_data.get("skill_validation_details", {}),
        "jd_comparison": analysis_data.get("jd_match_analysis") or analysis_data.get("jd_comparison"),
        "analysis_date": format_date(datetime.now().isoformat()),
    }

    rendered_docs = {}
    for template_name, key in [
        ("summary.html", "summary"),
        ("quick_actions.html", "quick_actions"),
        ("action_items.html", "action_items"),
        ("jd_comparison.html", "jd_comparison"),
    ]:
        try:
            tmpl = env.get_template(template_name)
            rendered_docs[key] = tmpl.render(context)
        except Exception as exc:
            logger.warning(f"Template rendering skipped for {template_name}: {exc}")

    return rendered_docs
