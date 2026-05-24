@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo Starting OntoChain
echo ============================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_project.ps1"

echo.
echo Startup command finished. You may close this window after the two service windows open.
pause >nul

