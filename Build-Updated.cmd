@echo off
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Build-Updated.ps1" -Validate
if errorlevel 1 exit /b 1
pause
