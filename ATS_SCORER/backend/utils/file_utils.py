import logging
import mimetypes
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar

LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("ats_resume_scorer")
logger.setLevel(logging.INFO)

if not logger.handlers:
    # File handler
    file_handler = logging.FileHandler(LOG_DIR / "ats_scorer.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(console_handler)


class ATSBaseError(Exception):
    """Base exception for ATS application."""
    def __init__(self, message: str, user_message: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.user_message = user_message or "An unexpected error occurred. Please try again."


class FileUploadError(ATSBaseError):
    pass


class FileValidationError(ATSBaseError):
    pass


class FileParsingError(ATSBaseError):
    pass


class TextExtractionError(ATSBaseError):
    pass


def log_error(error: Exception, context: Optional[str] = None) -> None:
    logger.error(f"Error in {context or 'unknown'}: {error}", exc_info=True)


def log_warning(message: str, context: Optional[str] = None) -> None:
    logger.warning(f"{context or 'ATS'}: {message}")


def log_info(message: str, context: Optional[str] = None) -> None:
    logger.info(f"{context or 'ATS'}: {message}")


T = TypeVar("T")


def with_fallback(
    primary_func: Callable[..., T],
    fallback_func: Callable[..., T],
    *args,
    log_fallback: bool = True,
    **kwargs,
) -> Tuple[T, bool]:
    """Run primary function; if it fails, safely invoke fallback function."""
    try:
        return primary_func(*args, **kwargs), False
    except Exception as primary_error:
        if log_fallback:
            log_warning(f"Primary method failed: {primary_error}. Attempting fallback...", context="fallback")
        try:
            return fallback_func(*args, **kwargs), True
        except Exception as fallback_error:
            log_error(fallback_error, context="fallback")
            raise


def detect_file_type(file_bytes: bytes, filename: str) -> Optional[str]:
    """
    Safely determine file type (.pdf, .docx, .doc, .txt) using magic byte signatures
    and filename extensions without requiring external C libraries on Windows.
    """
    ext = Path(filename).suffix.lower()

    # Magic byte header sniffing
    if file_bytes.startswith(b"%PDF"):
        return "pdf"
    if file_bytes.startswith(b"PK\x03\x04"):
        # ZIP archive - standard for DOCX
        if ext in (".docx", ".doc"):
            return "docx"
        return "docx"
    if file_bytes.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        # OLE compound document (legacy .doc)
        return "doc"

    # Extension-based mapping fallback
    ext_map = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".doc": "doc",
        ".txt": "txt",
    }
    if ext in ext_map:
        return ext_map[ext]

    # Standard library mimetypes
    guessed, _ = mimetypes.guess_type(filename)
    if guessed:
        if "pdf" in guessed:
            return "pdf"
        if "wordprocessingml" in guessed:
            return "docx"
        if "msword" in guessed:
            return "doc"
        if "text" in guessed:
            return "txt"

    return None


def get_default_grammar_results() -> Dict[str, Any]:
    return {
        "total_errors": 0,
        "critical_errors": [],
        "moderate_errors": [],
        "minor_errors": [],
        "grammar_score": 100.0,
        "penalty_applied": 0.0,
        "error_free_percentage": 100.0,
        "_component_status": "ok",
    }


def get_default_location_results() -> Dict[str, Any]:
    return {
        "location_found": False,
        "detected_locations": [],
        "privacy_risk": "none",
        "recommendations": ["No location privacy risks detected."],
        "penalty_applied": 0.0,
        "_component_status": "ok",
    }


def get_default_skill_validation_results() -> Dict[str, Any]:
    return {
        "validated_skills": [],
        "unvalidated_skills": [],
        "validation_percentage": 0.0,
        "skill_project_mapping": {},
        "validation_score": 0.0,
        "_component_status": "ok",
    }


def get_default_jd_comparison_results() -> Dict[str, Any]:
    return {
        "semantic_similarity": 0.0,
        "matched_keywords": [],
        "missing_keywords": [],
        "skills_gap": [],
        "match_percentage": 0.0,
        "_component_status": "ok",
    }
