Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$SetupScript = Join-Path $ProjectRoot "scripts\setup_env.ps1"

if (-not (Test-Path $VenvPython)) {
    Write-Host ".venv was not found. Running setup first..."
    & powershell -NoProfile -ExecutionPolicy Bypass -File $SetupScript
}

if (-not (Test-Path $VenvPython)) {
    throw "Virtual environment is still missing. Run SETUP_ENV.bat and check the error message."
}

$BackendCommand = "cd /d `"$ProjectRoot`" && `"$VenvPython`" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"
$FrontendCommand = "cd /d `"$ProjectRoot`" && `"$VenvPython`" -m streamlit run frontend/streamlit_app.py --server.address 127.0.0.1 --server.port 8501"

Write-Host "Opening FastAPI backend window..."
Start-Process cmd.exe -ArgumentList "/k", $BackendCommand

Start-Sleep -Seconds 3

Write-Host "Opening Streamlit frontend window..."
Start-Process cmd.exe -ArgumentList "/k", $FrontendCommand

Write-Host ""
Write-Host "OntoChain is starting."
Write-Host "Backend:  http://127.0.0.1:8000/docs"
Write-Host "Frontend: http://127.0.0.1:8501"
Write-Host ""
Write-Host "If the browser does not open automatically, copy the Frontend URL into your browser."

Start-Sleep -Seconds 3
Start-Process "http://127.0.0.1:8501"
