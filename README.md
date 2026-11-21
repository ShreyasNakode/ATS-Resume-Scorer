# 🎯 ATS Resume Scorer & Analyzer

> Production-grade Applicant Tracking System (ATS) Resume Analyzer built from scratch with **BERT (Bidirectional Encoder Representations from Transformers)**, **FastAPI**, **Streamlit**, **spaCy**, **Scikit-Learn**, **Clerk Authentication**, **PyPDF2**, and **Python-Docx**. Supports deployment to **AWS Elastic Beanstalk** and **Vercel**.

---

## 📁 Repository Overview

This repository is organized into the requested production structure:

```
ATS_SCORER/
├── backend/              FastAPI app, NLP services, API routes
├── frontend/             Streamlit app, views, components
├── jupyter notebooks/    Research and dataset prep (not used at runtime)
├── ml model/             Exported ML artifacts
├── requirements.txt      Combined backend + frontend dependencies
└── .env.example          Template for environment variables
```

---

## 📖 User Manual — How to Run on Your System

### ⚡ Option A: One-Line Terminal Command (Download + Install + Launch All)

Copy and paste **one** of the commands below into your terminal to clone the repository, install all Python & NLP dependencies, launch the **FastAPI Backend** (`http://localhost:8000`), and open the **Streamlit Frontend** (`http://localhost:8501`) automatically in your browser:

#### Windows (PowerShell)
```powershell
git clone https://github.com/ShreyasNakode/ATS-Resume-Scorer.git; cd "ATS-Resume-Scorer\ATS_SCORER"; pip install -r requirements.txt; python -m spacy download en_core_web_md; Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"; python -m streamlit run frontend/streamlit_app.py
```

#### Windows (Command Prompt / CMD)
```cmd
git clone https://github.com/ShreyasNakode/ATS-Resume-Scorer.git && cd ATS-Resume-Scorer\ATS_SCORER && pip install -r requirements.txt && python -m spacy download en_core_web_md && start cmd /k "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload" && python -m streamlit run frontend/streamlit_app.py
```

#### Linux / macOS / Git Bash
```bash
git clone https://github.com/ShreyasNakode/ATS-Resume-Scorer.git && cd ATS-Resume-Scorer/ATS_SCORER && pip install -r requirements.txt && python -m spacy download en_core_web_md && (python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &) && python -m streamlit run frontend/streamlit_app.py
```

---

### 🛠️ Option B: Step-by-Step Manual Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/ShreyasNakode/ATS-Resume-Scorer.git
cd ATS-Resume-Scorer/ATS_SCORER
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_md
```

#### 3. Run the FastAPI Backend (Terminal 1)
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/api/v1/health`

#### 4. Run the Streamlit Frontend (Terminal 2)
```bash
python -m streamlit run frontend/streamlit_app.py
```
- **Web Application**: Opens automatically at `http://localhost:8501`

For full architectural documentation, see [ATS_SCORER/README.md](ATS_SCORER/README.md).
