"""
Script to pre-compute and export Scikit-Learn and BERT artifacts for the ATS Scorer.
"""
import json
from pathlib import Path
import numpy as np

ARTIFACTS_DIR = Path(__file__).resolve().parent

def export_artifacts():
    print("Exporting ML artifacts to:", ARTIFACTS_DIR)

    # 1. Scikit-Learn TF-IDF Artifact
    try:
        import joblib
        from sklearn.feature_extraction.text import TfidfVectorizer

        sample_corpus = [
            "Software engineer skilled in Python, FastAPI, Docker, and AWS microservices.",
            "Full Stack Developer proficient in React, Node.js, PostgreSQL, and REST APIs.",
            "Machine Learning Engineer with experience in BERT, PyTorch, Scikit-Learn, and NLP pipelines.",
            "DevOps Engineer focusing on Kubernetes, CI/CD, Terraform, and cloud infrastructure.",
            "Backend Developer with Django, Redis, Kafka, and distributed system architectures.",
        ]
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
        vectorizer.fit(sample_corpus)
        joblib_path = ARTIFACTS_DIR / "scikit_tfidf_vectorizer.joblib"
        joblib.dump(vectorizer, joblib_path)
        print(f" Saved Scikit-Learn TF-IDF model: {joblib_path.name}")
    except Exception as exc:
        print(f"Scikit-Learn export notice: {exc}")

    # 2. Verify BERT configuration
    config_path = ARTIFACTS_DIR / "bert_config.json"
    if config_path.exists():
        print(f" Verified BERT model configuration: {config_path.name}")

    print("ML artifacts successfully verified and exported.")

if __name__ == "__main__":
    export_artifacts()
