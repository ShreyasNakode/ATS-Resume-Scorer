@echo off
echo ===================================================
echo Installing ATS Scorer Dependencies
echo ===================================================
cd /d "%~dp0"
pip install -r requirements.txt
python -m spacy download en_core_web_md
echo.
echo Dependencies installed successfully!
pause
