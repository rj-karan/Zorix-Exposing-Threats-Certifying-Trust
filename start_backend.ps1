# Windows PowerShell script to start the backend with UTF-8 encoding
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONLEGACYWINDOWSSTDIO = "0"

# Change to the project directory
Set-Location "C:\zorix\Zorix-Exposing-Threats-Certifying-Trust"

# Start the backend server
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
