import re
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = Any  # type: ignore

from backend.core.config import SCORE_WEIGHTS
from backend.services.bert_service import compute_skill_project_match
from backend.utils.matching import fuzzy_match_keywords

ZIP_CODE_PATTERN = r"\b\d{5}(?:-\d{4})?\b"
STREET_ADDRESS_PATTERN = (
    r"\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+"
    r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir|Way|Place|Pl)\b"
)


def _tier_score(n: float, tiers: List[Tuple[float, float]]) -> float:
    """Helper to calculate stepped tier score based on thresholds."""
    for threshold, pts in tiers:
        if n >= threshold:
            return pts
    return 0.0


def validate_skills_with_projects(
    skills: List[str],
    projects: List[Dict[str, Any]],
    experience_entries: List[Dict[str, Any]],
    embedder: Any,
    threshold: float = 0.55,
) -> Dict[str, Any]:
    """
    Validate whether claimed skills appear in projects or work experience
    using BERT semantic embeddings and exact matching.
    """
    if not skills:
        return {
            "validated_skills": [],
            "unvalidated_skills": [],
            "validation_percentage": 0.0,
            "skill_project_mapping": {},
            "validation_score": 0.0,
        }

    experience_text = " ".join(
        f"{e.get('job_title', '')} {e.get('company', '')} {e.get('description', '')}"
        for e in experience_entries
        if isinstance(e, dict)
    ).strip()

    validated_skills = []
    unvalidated_skills = []
    skill_project_mapping = {}

    for skill in skills:
        matching_projects = []
        max_sim = 0.0

        # Check projects
        for project in projects:
            p_text = f"{project.get('title', '')} {project.get('description', '')}"
            matched, sim = compute_skill_project_match(skill, p_text, embedder, threshold)
            max_sim = max(max_sim, sim)
            if matched:
                matching_projects.append(project.get("title", "Project"))

        # Check experience section
        if experience_text:
            matched, sim = compute_skill_project_match(skill, experience_text, embedder, threshold)
            max_sim = max(max_sim, sim)
            if matched and "Work Experience" not in matching_projects:
                matching_projects.append("Work Experience")

        if matching_projects:
            validated_skills.append({
                "skill": skill,
                "projects": matching_projects,
                "similarity": round(max_sim, 3),
            })
            skill_project_mapping[skill] = matching_projects
        else:
            unvalidated_skills.append(skill)
            skill_project_mapping[skill] = []

    validation_percentage = len(validated_skills) / len(skills)
    validation_score = round(validation_percentage * SCORE_WEIGHTS["skill_validation"], 1)

    return {
        "validated_skills": validated_skills,
        "unvalidated_skills": unvalidated_skills,
        "validation_percentage": round(validation_percentage, 3),
        "skill_project_mapping": skill_project_mapping,
        "validation_score": min(SCORE_WEIGHTS["skill_validation"], max(0.0, validation_score)),
    }


def _calc_formatting_score(parsed_resume: Dict[str, Any], text: str) -> float:
    """Score resume formatting and structure (Max 20 pts)."""
    score = 0.0
    exp = [e for e in parsed_resume.get("experience", []) if isinstance(e, dict)]
    edu = [e for e in parsed_resume.get("education", []) if isinstance(e, dict)]
    skills = parsed_resume.get("skills", [])
    summary = parsed_resume.get("professional_summary", "")
    projects = [p for p in parsed_resume.get("projects", []) if isinstance(p, dict)]

    if exp and any(e.get("job_title") or e.get("description") for e in exp):
        score += 3.0
    if edu:
        score += 2.0
    if len(skills) >= 3:
        score += 2.0
    if len(summary.strip()) > 30:
        score += 1.5
    if projects:
        score += 1.5

    # Bullet point counting
    bullet_count = sum(
        1 for line in text.split("\n")
        if re.match(r"^\s*[•\-\*\◦\u2022\u2023\u25E6]", line) or re.match(r"^\s*\d+\.", line)
    )
    score += _tier_score(bullet_count, [(15, 5.0), (10, 4.0), (5, 3.0), (3, 2.0), (1, 1.0)])

    # Section completeness
    filled = sum(1 for has in [bool(exp), bool(edu), bool(skills), bool(summary.strip()), bool(projects)] if has)
    score += _tier_score(filled, [(4, 5.0), (3, 4.0), (2, 3.0), (1, 2.0)])

    return min(SCORE_WEIGHTS["formatting"], max(0.0, round(score, 1)))


def _calc_keywords_score(
    resume_keywords: List[str],
    skills: List[str],
    jd_keywords: Optional[List[str]] = None,
) -> float:
    """Score keywords and technical skills density (Max 25 pts)."""
    score = 0.0
    score += _tier_score(len(resume_keywords), [(20, 10.0), (15, 8.0), (10, 6.0), (5, 4.0), (3, 2.0)])
    score += _tier_score(len(skills), [(15, 10.0), (10, 8.0), (7, 6.0), (5, 4.0), (3, 2.0)])

    if jd_keywords:
        all_terms = list(set(resume_keywords + skills))
        fuzzy_res = fuzzy_match_keywords(all_terms, jd_keywords, threshold=80)
        match_pct = len(fuzzy_res["matched"]) / len(jd_keywords) if jd_keywords else 0.0
        score += _tier_score(match_pct, [(0.7, 5.0), (0.5, 4.0), (0.3, 3.0), (0.2, 2.0), (0.1, 1.0)])
    elif len(resume_keywords) >= 10:
        score += 4.0

    return min(SCORE_WEIGHTS["keywords"], max(0.0, round(score, 1)))


def _calc_content_score(
    text: str,
    action_verbs: List[str],
    grammar_results: Dict[str, Any],
) -> float:
    """Score content quality, action verbs, and quantifiable metrics (Max 25 pts)."""
    score = 0.0
    score += _tier_score(len(action_verbs), [(15, 10.0), (10, 8.0), (7, 6.0), (5, 4.0), (3, 2.0)])

    # Quantifiable achievement metrics regex
    metric_patterns = [
        r"\d+%",
        r"\$\d+(?:,\d+)*(?:\.\d+)?[kKmMbB]?",
        r"\b\d+\+?\s*(?:users|clients|customers|projects|downloads|endpoints|requests)\b",
        r"\b(?:increased|decreased|improved|reduced|grew|saved|optimized|accelerated)\b(?:\s+\w+){0,3}\s+\d+",
        r"\b\d+x\b",
    ]
    achievement_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in metric_patterns)
    score += _tier_score(achievement_count, [(10, 8.0), (7, 6.0), (5, 5.0), (3, 3.0), (1, 2.0)])

    grammar_penalty = grammar_results.get("penalty_applied", 0.0)
    score += max(0.0, 7.0 - (grammar_penalty / 2.0))

    return min(SCORE_WEIGHTS["content"], max(0.0, round(score, 1)))


def _calc_ats_compatibility_score(
    text: str,
    location_results: Dict[str, Any],
    parsed_resume: Dict[str, Any],
) -> float:
    """Score ATS parsing compatibility, table complexity, and layout cleanliness (Max 15 pts)."""
    score = 15.0

    # Privacy penalty
    score -= location_results.get("penalty_applied", 0.0)

    # Box-drawing or complex decorative characters
    special_chars = len(re.findall(r"[│┤├┼┴┬╔╗╚╝═║╠╣╦╩╬★♦◆■●▪▲]", text))
    if special_chars > 20:
        score -= 2.0
    elif special_chars > 10:
        score -= 1.0

    exp = [e for e in parsed_resume.get("experience", []) if isinstance(e, dict)]
    edu = [e for e in parsed_resume.get("education", []) if isinstance(e, dict)]
    skills = parsed_resume.get("skills", [])

    if len(skills) >= 5 and (exp or edu):
        score += 1.0

    return min(SCORE_WEIGHTS["ats_compatibility"], max(0.0, round(score, 1)))


def _generate_score_interpretation(score: float) -> str:
    """Human-readable evaluation statement for overall score."""
    if score >= 90:
        return "Outstanding! Your resume is primed for top-tier ATS screening."
    if score >= 80:
        return "Strong! Your resume will pass the vast majority of ATS filters with high ranking."
    if score >= 70:
        return "Good. Well-structured with minor keyword or metric optimization needed."
    if score >= 60:
        return "Fair. Missing key quantifiable metrics or critical target job keywords."
    if score >= 50:
        return "Below Average. Substantial formatting or keyword gaps require attention."
    return "Needs Revision. Structural and keyword revisions needed to pass automated screening."


def calculate_overall_score(
    text: str,
    parsed_resume: Dict[str, Any],
    skills: List[str],
    keywords: List[str],
    action_verbs: List[str],
    skill_validation_results: Dict[str, Any],
    grammar_results: Dict[str, Any],
    location_results: Dict[str, Any],
    jd_keywords: Optional[List[str]] = None,
    experience_months: int = 0,
) -> Dict[str, Any]:
    """Calculate aggregate 0-100 ATS score and component breakdown."""
    formatting_score = _calc_formatting_score(parsed_resume, text)
    keywords_score = _calc_keywords_score(keywords, skills, jd_keywords)
    content_score = _calc_content_score(text, action_verbs, grammar_results)
    skill_validation_score = skill_validation_results.get("validation_score", 0.0)
    ats_compatibility_score = _calc_ats_compatibility_score(text, location_results, parsed_resume)

    # Weighted composite sum
    base_score = (
        formatting_score +
        keywords_score +
        content_score +
        skill_validation_score +
        ats_compatibility_score
    )

    bonuses = {}
    penalties = {}
    score = base_score

    # Skill validation bonus
    val_pct = skill_validation_results.get("validation_percentage", 0.0)
    if val_pct >= 0.85:
        bonuses["high_skill_validation"] = 2.0
        score += 2.0

    # JD gap penalty
    if jd_keywords:
        all_terms = list(set(keywords + skills))
        fuzzy_res = fuzzy_match_keywords(all_terms, jd_keywords, threshold=80)
        missing_pct = len(fuzzy_res["missing"]) / len(jd_keywords) if jd_keywords else 0.0
        if missing_pct > 0.65:
            penalties["high_keyword_gap"] = 8.0
            score -= 8.0
        elif missing_pct > 0.40:
            penalties["moderate_keyword_gap"] = 4.0
            score -= 4.0

    overall_score = float(np.clip(score, 0.0, 100.0))

    return {
        "overall_score": round(overall_score, 1),
        "formatting_score": formatting_score,
        "keywords_score": keywords_score,
        "content_score": content_score,
        "skill_validation_score": skill_validation_score,
        "ats_compatibility_score": ats_compatibility_score,
        "overall_interpretation": _generate_score_interpretation(overall_score),
        "penalties": penalties,
        "bonuses": bonuses,
    }


def generate_strengths(
    score_results: Dict[str, Any],
    skill_validation_results: Dict[str, Any],
    grammar_results: Dict[str, Any],
) -> List[str]:
    """Highlight positive aspects of candidate resume."""
    strengths = []
    if score_results.get("formatting_score", 0) >= 16:
        strengths.append("Clear structural hierarchy with well-organized sections and bullet points.")
    if score_results.get("keywords_score", 0) >= 20:
        strengths.append("Robust density of relevant technical skills and industry keywords.")
    if score_results.get("content_score", 0) >= 20:
        strengths.append("Strong usage of active verbs and measurable achievement outcomes.")
    val_pct = skill_validation_results.get("validation_percentage", 0.0) * 100
    if val_pct >= 70:
        strengths.append(f"{val_pct:.0f}% of listed skills are substantiated in real projects or work history.")
    if score_results.get("ats_compatibility_score", 0) >= 13:
        strengths.append("Clean ATS-compliant layout free of parsing-prohibitive tables or graphics.")

    if not strengths:
        strengths.append("Solid foundation with clear potential for high ATS optimization.")
    return strengths


def generate_critical_issues(
    score_results: Dict[str, Any],
    location_results: Dict[str, Any],
    skill_validation_results: Dict[str, Any],
) -> List[str]:
    """Identify severe roadblocks that could lead to automated ATS filtering."""
    issues = []
    if location_results.get("privacy_risk") == "high":
        issues.append("High privacy risk: Street address or zip code exposed on resume.")
    if score_results.get("formatting_score", 0) < 10:
        issues.append("Formatting deficient: Inconsistent section headings or absence of bullet lists.")
    if score_results.get("keywords_score", 0) < 12:
        issues.append("Low keyword match: Crucial job description keywords are missing.")
    if skill_validation_results.get("validation_percentage", 0) < 0.40:
        issues.append("Low skill validation: Over 60% of listed skills lack supporting project evidence.")
    return issues
