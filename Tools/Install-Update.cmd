@echo off
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-Update.ps1"
if errorlevel 1 (
    echo Installation failed. Read the error above.
    pause
    exit /b 1
)
pause
