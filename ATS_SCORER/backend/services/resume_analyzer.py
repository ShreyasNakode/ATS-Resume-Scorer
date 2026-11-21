import logging
from typing import Any, Dict, List, Optional

try:
    import spacy
    from spacy.language import Language
except ImportError:
    spacy = None  # type: ignore
    Language = Any  # type: ignore

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = Any  # type: ignore

from backend.services.ats_scorer import (
    calculate_overall_score,
    generate_critical_issues,
    generate_strengths,
    validate_skills_with_projects,
)
from backend.services.feedback_engine import analyze_issues, generate_issues_summary
from backend.services.ml_matcher import compare_resume_with_jd_hybrid
from backend.services.recommendation_engine import generate_recommendations
from backend.services.rule_parser import parse_job_description_hybrid, parse_resume_hybrid
from backend.services.spacy_service import detect_location_privacy, extract_action_verbs, extract_keywords_and_phrases
from backend.utils.file_utils import get_default_grammar_results

logger = logging.getLogger("ats_resume_scorer")


def analyze_full_resume(
    resume_text: str,
    nlp: Any,
    embedder: Any,
    job_description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Complete analysis pipeline combining BERT semantic embeddings,
    spaCy linguistic entity recognition, Scikit-Learn matching, and multi-tier scoring.
    """
    # 1. Parse Resume into Structured Sections
    parsed_resume = parse_resume_hybrid(resume_text)
    skills = parsed_resume.get("skills", [])
    projects = parsed_resume.get("projects", [])
    experience = parsed_resume.get("experience", [])

    # 2. Extract Action Verbs and Linguistic Keywords using spaCy
    action_verbs = parsed_resume.get("action_verbs") or extract_action_verbs(resume_text, nlp)
    keywords = parsed_resume.get("keywords") or extract_keywords_and_phrases(resume_text, nlp)

    # 3. Contact Info
    contact_info = {
        "email": parsed_resume.get("email"),
        "phone": parsed_resume.get("phone"),
        "linkedin": parsed_resume.get("linkedin"),
        "github": parsed_resume.get("github"),
    }

    # 4. BERT-Powered Skill Validation against Projects & Experience
    skill_validation = validate_skills_with_projects(
        skills=skills,
        projects=projects,
        experience_entries=experience,
        embedder=embedder,
        threshold=0.55,
    )

    # 5. Hybrid JD Comparison (if provided)
    jd_comparison_result = None
    jd_keywords = None
    if job_description and job_description.strip():
        parsed_jd = parse_job_description_hybrid(job_description.strip())
        jd_keywords = list(set(
            parsed_jd.get("keywords", []) +
            parsed_jd.get("required_skills", []) +
            parsed_jd.get("preferred_skills", [])
        ))
        jd_comparison_result = compare_resume_with_jd_hybrid(
            resume_text=resume_text,
            resume_keywords=keywords,
            resume_skills=skills,
            jd_text=job_description.strip(),
            jd_keywords=jd_keywords,
            embedder=embedder,
        )

    # 6. Location Privacy & Grammar Detection
    location_results = detect_location_privacy(resume_text, nlp)
    grammar_results = get_default_grammar_results()

    # 7. Multi-Tier Score Calculation (0 - 100)
    scores = calculate_overall_score(
        text=resume_text,
        parsed_resume=parsed_resume,
        skills=skills,
        keywords=keywords,
        action_verbs=action_verbs,
        skill_validation_results=skill_validation,
        grammar_results=grammar_results,
        location_results=location_results,
        jd_keywords=jd_keywords,
    )

    # 8. Detailed Diagnostics & Feedback
    detailed_feedback = analyze_issues(
        resume_text=resume_text,
        parsed_resume=parsed_resume,
        skills=skills,
        projects=projects,
        action_verbs=action_verbs,
        skill_validation=skill_validation,
        scores=scores,
        contact_info=contact_info,
    )
    issues_summary = generate_issues_summary(detailed_feedback)

    # 9. Recommendations
    recommendations = generate_recommendations(
        score_results=scores,
        skill_validation_results=skill_validation,
        jd_comparison=jd_comparison_result,
    )

    # 10. Strengths & Critical Warnings
    strengths = generate_strengths(scores, skill_validation, grammar_results)
    critical_issues = generate_critical_issues(scores, location_results, skill_validation)

    # Skill validation detail format
    validated_raw = skill_validation.get("validated_skills", [])
    unvalidated_raw = skill_validation.get("unvalidated_skills", [])
    total_skills = len(validated_raw) + len(unvalidated_raw)
    val_pct = round((len(validated_raw) / total_skills * 100.0) if total_skills > 0 else 0.0, 1)

    skill_validation_details = {
        "validated": validated_raw,
        "unvalidated": unvalidated_raw,
        "total": total_skills,
        "validated_count": len(validated_raw),
        "validation_pct": val_pct,
    }

    return {
        "ATS_score": scores["overall_score"],
        "ats_score": scores["overall_score"],
        "component_scores": {
            "formatting": scores["formatting_score"],
            "keywords": scores["keywords_score"],
            "content": scores["content_score"],
            "skill_validation": scores["skill_validation_score"],
            "ats_compatibility": scores["ats_compatibility_score"],
        },
        "issues_summary": issues_summary,
        "detailed_feedback": detailed_feedback,
        "jd_match_analysis": jd_comparison_result,
        "jd_comparison": jd_comparison_result,
        "skill_validation_details": skill_validation_details,
        "recommendations": recommendations,
        "skills": skills,
        "matched_keywords": (
            jd_comparison_result.get("matched_keywords", [])
            if jd_comparison_result else list(keywords[:20])
        ),
        "missing_keywords": (
            jd_comparison_result.get("missing_keywords", [])
            if jd_comparison_result else []
        ),
        "suggestions": issues_summary[:5],
        "strengths": strengths,
        "critical_issues": critical_issues,
        "interpretation": scores.get("overall_interpretation", ""),
    }
