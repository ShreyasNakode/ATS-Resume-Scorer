@echo off
echo ===================================================
echo Starting ATS Resume Scorer Frontend (Streamlit)
echo ===================================================
cd /d "%~dp0ATS_SCORER"
streamlit run frontend/streamlit_app.py
pause
