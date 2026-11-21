import logging
import re
from typing import Any, Dict, List, Optional, Set
import spacy
from spacy.language import Language

from backend.core.config import SPACY_MODEL_PRIMARY, SPACY_MODEL_SECONDARY

logger = logging.getLogger("ats_resume_scorer")

_nlp_cache: Optional[Language] = None

ZIP_CODE_PATTERN = r"\b\d{5}(?:-\d{4})?\b"
STREET_ADDRESS_PATTERN = (
    r"\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+"
    r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir|Way|Place|Pl)\b"
)

# Common action verbs for ATS resumes
ACTION_VERB_ROOTS = {
    "achieve", "acquire", "adapt", "address", "administer", "advise", "allocate", "analyze",
    "appraise", "architect", "assemble", "assess", "audit", "automate", "author", "benchmark",
    "budget", "build", "calculate", "centralize", "champion", "clarify", "coach", "collaborate",
    "communicate", "compile", "compose", "compute", "conceive", "conduct", "configure", "consolidate",
    "construct", "coordinate", "counsel", "create", "customize", "debug", "decrease", "delegate",
    "deliver", "deploy", "design", "determine", "develop", "devise", "diagnose", "direct",
    "discover", "distribute", "diversify", "document", "draft", "drive", "eliminate", "enable",
    "engineer", "enhance", "establish", "evaluate", "exceed", "execute", "expand", "expedite",
    "fabricate", "facilitate", "finalize", "forecast", "formulate", "foster", "fulfill", "generate",
    "govern", "grow", "guide", "harness", "head", "hire", "identify", "implement", "improve",
    "increase", "initiate", "innovate", "inspect", "inspire", "install", "institute", "instruct",
    "integrate", "interface", "interpret", "interview", "introduce", "invent", "investigate",
    "launch", "lead", "leverage", "liaise", "localize", "maintain", "manage", "maximize",
    "measure", "mentor", "migrate", "minimize", "modernize", "modify", "monitor", "motivate",
    "negotiate", "orchestrate", "organize", "originate", "overhaul", "oversee", "partner", "perform",
    "pilot", "pioneer", "plan", "prepare", "present", "prioritize", "produce", "program",
    "promote", "propose", "publish", "quantify", "re-engineer", "realign", "rebuild", "recommend",
    "reconcile", "redesign", "reduce", "refactor", "refine", "reorganize", "replace", "report",
    "research", "resolve", "restructure", "retrieve", "revamp", "review", "revitalize", "scale",
    "schedule", "secure", "select", "simplify", "solve", "spearhead", "standardize", "streamline",
    "strengthen", "structure", "supervise", "synthesize", "systematize", "target", "test", "track",
    "train", "transform", "transition", "troubleshoot", "unify", "upgrade", "utilize", "validate",
    "verify", "visualize", "yield",
}


def get_spacy_nlp() -> Language:
    """Load or retrieve cached spaCy language model."""
    global _nlp_cache
    if _nlp_cache is not None:
        return _nlp_cache

    try:
        _nlp_cache = spacy.load(SPACY_MODEL_PRIMARY)
        logger.info(f"Loaded primary spaCy model: {SPACY_MODEL_PRIMARY}")
        return _nlp_cache
    except OSError:
        logger.warning(f"{SPACY_MODEL_PRIMARY} not found. Attempting {SPACY_MODEL_SECONDARY}...")
        try:
            _nlp_cache = spacy.load(SPACY_MODEL_SECONDARY)
            logger.info(f"Loaded secondary spaCy model: {SPACY_MODEL_SECONDARY}")
            return _nlp_cache
        except OSError:
            logger.warning("No spaCy model installed. Initializing spacy English blank pipeline.")
            _nlp_cache = spacy.blank("en")
            if "sentencizer" not in _nlp_cache.pipe_names:
                _nlp_cache.add_pipe("sentencizer")
            return _nlp_cache


def detect_location_privacy(text: str, nlp: Optional[Language] = None) -> Dict[str, Any]:
    """
    Detect location mentions, physical addresses, and zip codes for privacy risk scoring.
    """
    spacy_model = nlp or get_spacy_nlp()
    locations = []

    # 1. spaCy Named Entity Recognition (GPE / LOC)
    if "ner" in spacy_model.pipe_names:
        doc = spacy_model(text[:5000])
        for ent in doc.ents:
            if ent.label_ in ("GPE", "LOC"):
                locations.append({"text": ent.text, "type": ent.label_.lower(), "start": ent.start_char})

    # 2. Regex for Street Address
    for match in re.finditer(STREET_ADDRESS_PATTERN, text, re.IGNORECASE):
        locations.append({"text": match.group(), "type": "address", "start": match.start()})

    # 3. Regex for Postal / ZIP Codes
    for match in re.finditer(ZIP_CODE_PATTERN, text):
        locations.append({"text": match.group(), "type": "zip", "start": match.start()})

    has_address = any(loc["type"] == "address" for loc in locations)
    has_zip = any(loc["type"] == "zip" for loc in locations)

    if has_address and has_zip:
        privacy_risk, penalty = "high", 5.0
    elif has_address or has_zip:
        privacy_risk, penalty = "high", 4.0
    elif len(locations) > 3:
        privacy_risk, penalty = "medium", 3.0
    elif locations:
        privacy_risk, penalty = "low", 2.0
    else:
        privacy_risk, penalty = "none", 0.0

    recommendations = []
    if not locations:
        recommendations.append("No privacy concerns detected.")
    if has_address:
        recommendations.append("Remove full physical street address; modern ATS only requires City, State.")
    if has_zip:
        recommendations.append("Remove postal/zip code to minimize bias and preserve privacy.")
    if privacy_risk in ("low", "medium") and not has_address and not has_zip:
        recommendations.append("Keep location limited to 'City, State' in your header.")

    return {
        "location_found": len(locations) > 0,
        "detected_locations": locations,
        "privacy_risk": privacy_risk,
        "recommendations": recommendations,
        "penalty_applied": penalty,
    }


def extract_action_verbs(text: str, nlp: Optional[Language] = None) -> List[str]:
    """Extract strong action verbs used in resume bullet points using spaCy linguistic tagging."""
    spacy_model = nlp or get_spacy_nlp()
    found_verbs: Set[str] = set()

    # Fast word-boundary search for common action verb roots
    text_lower = text.lower()
    for verb in ACTION_VERB_ROOTS:
        # Match past tense or base form (e.g., develop, developed, developing)
        pattern = rf"\b{re.escape(verb)}(?:ed|d|ing|s)?\b"
        if re.search(pattern, text_lower):
            found_verbs.add(verb)

    # Use spaCy POS tagging if available
    if "tagger" in spacy_model.pipe_names or "pos" in spacy_model.pipe_names:
        doc = spacy_model(text[:6000])
        for token in doc:
            if token.pos_ == "VERB" and len(token.lemma_) > 3:
                lemma = token.lemma_.lower()
                if lemma in ACTION_VERB_ROOTS:
                    found_verbs.add(lemma)

    return sorted(list(found_verbs))


def extract_keywords_and_phrases(text: str, nlp: Optional[Language] = None) -> List[str]:
    """Extract candidate keywords, technical terms, and noun phrases using spaCy."""
    spacy_model = nlp or get_spacy_nlp()
    keywords: Set[str] = set()

    doc = spacy_model(text[:8000])

    # 1. Named Entities
    if "ner" in spacy_model.pipe_names:
        for ent in doc.ents:
            if ent.label_ in ("ORG", "PRODUCT", "WORK_OF_ART", "LANGUAGE"):
                val = ent.text.strip()
                if 2 <= len(val) <= 35 and not val.isnumeric():
                    keywords.add(val)

    # 2. Noun chunks
    try:
        for chunk in doc.noun_chunks:
            cleaned = chunk.text.strip()
            words = cleaned.split()
            if 1 <= len(words) <= 3 and len(cleaned) >= 3:
                if not any(stop in cleaned.lower() for stop in ["i", "we", "my", "our", "the", "a", "an"]):
                    keywords.add(cleaned)
    except Exception:
        pass

    return sorted(list(keywords))[:40]
