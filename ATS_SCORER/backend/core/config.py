import os
from pathlib import Path
from typing import Dict, Set

# Attempt to load .env from project root
try:
    from dotenv import load_dotenv
    _ENV_PATH = Path(__file__).resolve().parents[2] / '.env'
    if _ENV_PATH.exists():
        load_dotenv(_ENV_PATH)
    else:
        load_dotenv()
except ImportError:
    pass

# API Metadata
APP_TITLE = "BERT ATS Resume Analyzer & Scorer API"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = (
    "Production-grade ATS Resume Analyzer powered by BERT "
    "(Bidirectional Encoder Representations from Transformers), spaCy, and Scikit-Learn."
)

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000,https://*.streamlit.app",
    ).split(",")
    if origin.strip()
]

# File upload limits
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

SUPPORTED_MIME_TYPES: Dict[str, str] = {
    'application/pdf': 'pdf',
    'application/msword': 'doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'text/plain': 'txt',
}

SUPPORTED_EXTENSIONS: Set[str] = {'.pdf', '.doc', '.docx', '.txt'}

# NLP & BERT Configuration
SPACY_MODEL_PRIMARY = os.getenv("SPACY_MODEL_PRIMARY", "en_core_web_md")
SPACY_MODEL_SECONDARY = os.getenv("SPACY_MODEL_SECONDARY", "en_core_web_sm")
SENTENCE_TRANSFORMER_MODEL = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")
BERT_MODEL_NAME = os.getenv("BERT_MODEL_NAME", "bert-base-uncased")

# Multi-dimensional ATS Score Weights (Total: 100)
SCORE_WEIGHTS = {
    "formatting": 20.0,
    "keywords": 25.0,
    "content": 25.0,
    "skill_validation": 15.0,
    "ats_compatibility": 15.0,
}

# Job Description Match Composition
JD_KEYWORD_WEIGHT = 0.60
JD_SEMANTIC_WEIGHT = 0.40

# Clerk Authentication Configuration
CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY", "")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL", "")
CLERK_PEM_PUBLIC_KEY = os.getenv("CLERK_PEM_PUBLIC_KEY", "")
ENABLE_DEMO_AUTH = os.getenv("ENABLE_DEMO_AUTH", "true").lower() in ("true", "1", "yes")

# Database & Storage
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ats_history.db")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

# Optional LLM integration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
