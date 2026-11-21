import logging
from typing import Any, Dict, List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = Any  # type: ignore

from backend.services.bert_service import calculate_semantic_similarity
from backend.utils.matching import fuzzy_match_keywords, normalize_skill

logger = logging.getLogger("ats_resume_scorer")


def calculate_tfidf_similarity(text1: str, text2: str) -> float:
    """
    Calculate TF-IDF n-gram cosine similarity using Scikit-Learn.
    Captures exact keyword frequency, unigrams, and bigrams.
    """
    if not text1 or not text2:
        return 0.0

    try:
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            sublinear_tf=True,
            max_features=5000,
        )
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        return float(np.clip(sim[0][0], 0.0, 1.0))
    except Exception as exc:
        logger.warning(f"Scikit-Learn TF-IDF calculation error: {exc}")
        return 0.0


def compare_resume_with_jd_hybrid(
    resume_text: str,
    resume_keywords: List[str],
    resume_skills: List[str],
    jd_text: str,
    jd_keywords: List[str],
    embedder: Any,
) -> Dict[str, Any]:
    """
    Perform deep hybrid comparison between Resume and Job Description using:
    1. Scikit-Learn TF-IDF Cosine Similarity
    2. BERT Bidirectional Transformer Dense Semantic Similarity
    3. Keyword Overlap & Skill Gap Analysis
    """
    # 1. BERT Dense Semantic Similarity
    bert_semantic_sim = calculate_semantic_similarity(resume_text, jd_text, embedder)

    # 2. Scikit-Learn TF-IDF Similarity
    tfidf_sim = calculate_tfidf_similarity(resume_text, jd_text)

    # 3. Fuzzy Keyword Overlap
    all_resume_terms = list(set(resume_keywords + resume_skills))
    fuzzy_results = fuzzy_match_keywords(all_resume_terms, jd_keywords, threshold=80)
    matched_keywords = fuzzy_results["matched"]
    missing_keywords = fuzzy_results["missing"]

    keyword_overlap = (
        len(matched_keywords) / len(jd_keywords) if jd_keywords else 0.0
    )

    # Weighted composite match percentage:
    # 50% BERT Semantic Similarity + 20% Scikit-Learn TF-IDF + 30% Exact/Fuzzy Keyword Overlap
    composite_match = (
        (bert_semantic_sim * 0.50) +
        (tfidf_sim * 0.20) +
        (keyword_overlap * 0.30)
    ) * 100.0

    match_percentage = float(np.clip(composite_match, 0.0, 100.0))

    # Identify skill gaps
    resume_norm = {normalize_skill(s) for s in all_resume_terms}
    skills_gap = [
        kw for kw in missing_keywords
        if normalize_skill(kw) not in resume_norm
    ][:15]

    return {
        "match_percentage": round(match_percentage, 1),
        "semantic_similarity": round(bert_semantic_sim, 3),
        "tfidf_similarity": round(tfidf_sim, 3),
        "matched_keywords": matched_keywords[:25],
        "missing_keywords": missing_keywords[:20],
        "skills_gap": skills_gap,
    }
