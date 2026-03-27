@echo off
REM Windows Batch file to start backend with UTF-8 encoding
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=0
chcp 65001 >nul

cd /d "C:\zorix\Zorix-Exposing-Threats-Certifying-Trust"
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
pause
