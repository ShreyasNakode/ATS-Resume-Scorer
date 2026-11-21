import logging
from typing import List, Optional, Tuple, Union
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

from backend.core.config import SENTENCE_TRANSFORMER_MODEL

logger = logging.getLogger("ats_resume_scorer")

_model_cache: Optional[SentenceTransformer] = None


def get_bert_model(model_name: Optional[str] = None) -> SentenceTransformer:
    """Load or retrieve cached BERT / SentenceTransformer model."""
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    target_model = model_name or SENTENCE_TRANSFORMER_MODEL
    logger.info(f"Loading BERT SentenceTransformer model: {target_model}")
    try:
        _model_cache = SentenceTransformer(target_model)
        logger.info(f"Successfully loaded {target_model}")
        return _model_cache
    except Exception as exc:
        logger.warning(f"Could not load {target_model}: {exc}. Falling back to 'all-MiniLM-L6-v2'")
        _model_cache = SentenceTransformer("all-MiniLM-L6-v2")
        return _model_cache


def compute_bert_embeddings(
    texts: Union[str, List[str]],
    model: Optional[SentenceTransformer] = None,
) -> np.ndarray:
    """
    Encode texts into dense vector representations using BERT bidirectional transformer layers.
    """
    bert = model or get_bert_model()
    if isinstance(texts, str):
        texts = [texts]
    if not texts:
        return np.empty((0, 384))
    embeddings = bert.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return embeddings


def calculate_semantic_similarity(
    text1: str,
    text2: str,
    model: Optional[SentenceTransformer] = None,
) -> float:
    """
    Compute Bidirectional Cosine Semantic Similarity between two texts using BERT and Scikit-Learn.
    """
    if not text1 or not text2:
        return 0.0

    bert = model or get_bert_model()
    # Truncate to first 4,000 characters to stay within BERT token window comfortably
    emb1 = bert.encode([text1[:4000]], convert_to_numpy=True)
    emb2 = bert.encode([text2[:4000]], convert_to_numpy=True)

    # Scikit-Learn Cosine Similarity
    sim_matrix = cosine_similarity(emb1, emb2)
    similarity = float(sim_matrix[0][0])
    return float(np.clip(similarity, 0.0, 1.0))


def compute_skill_project_match(
    skill: str,
    project_text: str,
    model: Optional[SentenceTransformer] = None,
    threshold: float = 0.55,
) -> Tuple[bool, float]:
    """
    Determine if a skill is evidenced in a project description using exact match or BERT semantic similarity.
    """
    if not skill or not project_text:
        return False, 0.0

    skill_lower = skill.lower()
    text_lower = project_text.lower()

    # 1. Fast substring match (O(N))
    if skill_lower in text_lower:
        return True, 1.0

    # 2. Semantic matching with BERT embeddings
    sim = calculate_semantic_similarity(skill, project_text, model)
    return sim >= threshold, sim
