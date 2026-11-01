@echo off
cd /d "%~dp0"
call "%~dp0setup.bat" || exit /b 1
.venv\Scripts\python.exe train.py %*
if errorlevel 1 pause
