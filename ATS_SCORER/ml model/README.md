# ML Model Artifacts & BERT Architecture

This folder contains pre-computed ML artifacts, taxonomies, and architectural configuration for the ATS Resume Scorer.

## Models Included

1. **BERT (Bidirectional Encoder Representations from Transformers)**:
   - Architecture: `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors) or `bert-base-uncased` (768 dimensions).
   - Deep contextual sentence and phrase embeddings.
   - Used for semantic similarity comparison between candidate resume text, project bullet points, and target job descriptions.
   - Evaluated via Cosine Similarity (`sklearn.metrics.pairwise.cosine_similarity`).

2. **Scikit-Learn TF-IDF N-Gram Vectorizer**:
   - Captures unigrams and bigrams with sublinear term-frequency scaling.
   - Balances deep semantic matching with precise technical keyword frequency.

3. **Skills Taxonomy**:
   - `skills_taxonomy.json`: Hierarchical taxonomy of 500+ engineering, cloud, database, AI, and tool skills.

## Pre-generating Artifacts

To re-export artifacts, run:
```bash
python "ml model/export_artifacts.py"
```
