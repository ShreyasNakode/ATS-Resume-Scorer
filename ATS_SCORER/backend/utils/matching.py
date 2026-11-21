from typing import Dict, List
from rapidfuzz import fuzz

SKILL_ALIASES: Dict[str, str] = {
    "reactjs": "react",
    "react.js": "react",
    "angularjs": "angular",
    "vuejs": "vue",
    "vue.js": "vue",
    "nextjs": "next.js",
    "next.js": "next.js",
    "nodejs": "node.js",
    "node.js": "node.js",
    "node": "node.js",
    "expressjs": "express",
    "express.js": "express",
    "springboot": "spring boot",
    "spring-boot": "spring boot",
    "golang": "go",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "k8s": "kubernetes",
    "sklearn": "scikit-learn",
    "scikitlearn": "scikit-learn",
    "postgres": "postgresql",
    "dotnet": ".net",
    ".net core": ".net",
    "tailwindcss": "tailwind",
    "amazon web services": "aws",
    "aws cloud": "aws",
    "google cloud platform": "gcp",
    "google cloud": "gcp",
    "azure cloud": "azure",
    "pyspark": "spark",
    "huggingface": "hugging face",
    "bert": "bert",
    "fastapi": "fastapi",
    "streamlit": "streamlit",
    "restful api": "rest api",
    "rest apis": "rest api",
    "ci/cd": "cicd",
}


def normalize_skill(skill: str) -> str:
    """Normalize skill name using lowercasing, punctuation stripping, and alias mapping."""
    cleaned = skill.strip().lower()
    return SKILL_ALIASES.get(cleaned, cleaned)


def fuzzy_match_keywords(
    resume_keywords: List[str],
    jd_keywords: List[str],
    threshold: int = 80,
) -> Dict[str, List[str]]:
    """
    Compare resume keywords against job description keywords using canonical normalization
    and rapidfuzz token similarity.
    """
    resume_normalized = {normalize_skill(kw): kw for kw in resume_keywords if kw}
    jd_normalized = {normalize_skill(kw): kw for kw in jd_keywords if kw}

    matched_jd_originals = []
    missing_jd_originals = []

    for jd_canon, jd_original in jd_normalized.items():
        # 1. Exact canonical or substring match
        if jd_canon in resume_normalized:
            matched_jd_originals.append(jd_original)
            continue

        # 2. Fuzzy match against all resume canonical names
        best_score = 0
        for resume_canon in resume_normalized:
            score = fuzz.token_sort_ratio(jd_canon, resume_canon)
            best_score = max(best_score, score)

        if best_score >= threshold:
            matched_jd_originals.append(jd_original)
        else:
            missing_jd_originals.append(jd_original)

    return {
        "matched": sorted(list(set(matched_jd_originals))),
        "missing": sorted(list(set(missing_jd_originals))),
    }
