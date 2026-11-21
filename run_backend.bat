@echo off
echo ===================================================
echo Starting ATS Resume Scorer Backend (FastAPI + BERT)
echo ===================================================
cd /d "%~dp0ATS_SCORER"
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
pause
