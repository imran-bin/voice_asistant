# JARVIS AI Launcher Script for PowerShell
$Host.UI.RawUI.WindowTitle = "JARVIS AI Voice Assistant"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       JARVIS AI - Local Ollama Voice Assistant" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Determine python command (prefer py -3.13 or py -3 if available)
$pythonCmd = "python"
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py -3"
}

# Create virtual environment if missing
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "[1/3] Creating virtual environment (venv)..." -ForegroundColor Yellow
    Invoke-Expression "$pythonCmd -m venv venv"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment."
        exit $LASTEXITCODE
    }
}

# Activate environment
Write-Host "[2/3] Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install requirements
Write-Host "[3/3] Checking and installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

# Default model
if (-not $env:OLLAMA_MODEL) {
    $env:OLLAMA_MODEL = "llama3.2:latest"
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  JARVIS is starting at: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "  Active Model: $env:OLLAMA_MODEL" -ForegroundColor Green
Write-Host "  Press Ctrl+C to stop the server" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""

# Launch browser
Start-Process "http://127.0.0.1:8000"

# Start uvicorn server
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
