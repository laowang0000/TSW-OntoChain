Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Requirements = Join-Path $ProjectRoot "requirements.txt"

function Invoke-ProjectPython {
    param([string[]]$Arguments)
    & $VenvPython @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed: $($Arguments -join ' ')"
    }
}

Write-Host "Project root: $ProjectRoot"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating virtual environment: .venv"
    $PyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($PyLauncher) {
        & py -3 -m venv .venv
    }
    else {
        & python -m venv .venv
    }

    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $VenvPython)) {
        throw "Could not create .venv. Please install Python 3.12 or make sure python is available on PATH."
    }
}
else {
    Write-Host "Virtual environment already exists: .venv"
}

Write-Host "Upgrading pip"
Invoke-ProjectPython @("-m", "pip", "install", "--upgrade", "pip")

Write-Host "Installing project dependencies"
Invoke-ProjectPython @("-m", "pip", "install", "-r", $Requirements)

Write-Host "Checking important imports"
Invoke-ProjectPython @("-c", "import fastapi, rdflib, streamlit, pandas, pyvis, pytest; print('OntoChain environment OK')")

Write-Host ""
Write-Host "Environment setup complete."
Write-Host "Next step: double-click START_ONTOCHAIN.bat"

