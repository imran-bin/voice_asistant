@echo off
title JARVIS AI Assistant
echo ========================================================
echo         JARVIS AI - Local Ollama Voice Assistant
echo ========================================================
echo.

cd /d "%~dp0"

:: Check for Python launcher
where py >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py -3
) else (
    set PYTHON_CMD=python
)

:: Create virtual environment if it doesn't exist
if not exist "venv\Scripts\activate.bat" (
    echo [1/3] Creating virtual environment...
    %PYTHON_CMD% -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create venv. Please ensure Python 3.10+ is installed.
        pause
        exit /b %errorlevel%
    )
)

:: Activate environment
echo [2/3] Activating virtual environment...
call venv\Scripts\activate.bat

:: Install / verify dependencies
echo [3/3] Checking dependencies...
pip install -r requirements.txt --quiet

:: Set default model environment variable if not already set
if "%OLLAMA_MODEL%"=="" (
    set OLLAMA_MODEL=llama3.2:latest
)

echo.
echo ========================================================
echo  JARVIS is starting at http://127.0.0.1:8000
echo  Press Ctrl+C to stop the server
echo ========================================================
echo.

:: Open browser automatically after a short delay
start "" http://127.0.0.1:8000

:: Start Uvicorn
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause
