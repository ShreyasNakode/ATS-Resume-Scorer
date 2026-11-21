import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.core.config import (
    ALLOWED_ORIGINS,
    APP_DESCRIPTION,
    APP_TITLE,
    APP_VERSION,
    SENTENCE_TRANSFORMER_MODEL,
    SPACY_MODEL_PRIMARY,
    SPACY_MODEL_SECONDARY,
)

logger = logging.getLogger("ats_resume_scorer")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager: pre-loads BERT and spaCy models into app state.
    """
    logger.info("Initializing BERT ATS Resume Analyzer...")

    # 1. Load spaCy NLP Pipeline
    logger.info(f"Loading spaCy NLP model: {SPACY_MODEL_PRIMARY}")
    import spacy
    try:
        app.state.nlp = spacy.load(SPACY_MODEL_PRIMARY)
        logger.info(f"Loaded primary spaCy model '{SPACY_MODEL_PRIMARY}'.")
    except OSError:
        try:
            app.state.nlp = spacy.load(SPACY_MODEL_SECONDARY)
            logger.info(f"Loaded fallback spaCy model '{SPACY_MODEL_SECONDARY}'.")
        except OSError:
            logger.warning("No standard spaCy model found. Falling back to blank English tokenizer pipeline.")
            app.state.nlp = spacy.blank("en")
            if "sentencizer" not in app.state.nlp.pipe_names:
                app.state.nlp.add_pipe("sentencizer")

    # 2. Load BERT Embedder (SentenceTransformer)
    logger.info(f"Loading BERT SentenceTransformer: {SENTENCE_TRANSFORMER_MODEL}")
    try:
        from sentence_transformers import SentenceTransformer
        app.state.embedder = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
        logger.info(f"Loaded BERT model '{SENTENCE_TRANSFORMER_MODEL}'.")
    except Exception as exc:
        logger.warning(f"Could not load SentenceTransformer ({exc}). Initializing lightweight BERT fallback.")
        from sentence_transformers import SentenceTransformer
        app.state.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    logger.info("BERT ATS Engine is fully initialized and ready.")
    yield
    logger.info("Shutting down BERT ATS Engine.")


app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Cross-Origin Resource Sharing (CORS) Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in ALLOWED_ORIGINS else ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "name": APP_TITLE,
        "version": APP_VERSION,
        "technologies": [
            "FastAPI",
            "BERT (Bidirectional Encoder Representations from Transformers)",
            "spaCy NLP",
            "Scikit-Learn (TF-IDF & Cosine Similarity)",
            "Clerk Authentication",
            "PyPDF2 & Python-Docx Document Parsers",
        ],
        "endpoints": {
            "POST   /api/v1/analyze-resume": "Submit resume (PDF/DOCX) + optional JD for BERT scoring",
            "GET    /api/v1/health":         "Health check verifying model states",
            "GET    /api/v1/history":        "Retrieve authenticated user's analysis history",
            "DELETE /api/v1/history/:id":    "Delete history record",
            "POST   /api/v1/generate-pdf":   "Generate PDF report",
            "GET    /docs":                  "Interactive Swagger API Documentation",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
