@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo OntoChain environment setup
echo ============================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup_env.ps1"

echo.
echo Setup finished. Press any key to close this window.
pause >nul

