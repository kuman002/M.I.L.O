# MILO - PowerShell Setup Script
# Installs dependencies and sets up the environment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MILO Setup Script" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.10+ from https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ $pythonVersion" -ForegroundColor Green

# Upgrade pip
Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
Write-Host "✓ pip upgraded" -ForegroundColor Green

# Install requirements
Write-Host "`nInstalling dependencies from requirements.txt..." -ForegroundColor Yellow
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n⚠ Some packages failed to install." -ForegroundColor Yellow
    Write-Host "Trying alternative installation for pyaudio..." -ForegroundColor Yellow
    
    # Try pipwin for pyaudio on Windows
    pip install pipwin
    pipwin install pyaudio
}

# Check PyAudio specifically (common issue on Windows)
Write-Host "`nVerifying PyAudio installation..." -ForegroundColor Yellow
$pyaudioCheck = python -c "import pyaudio" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ PyAudio installed successfully" -ForegroundColor Green
} else {
    Write-Host "⚠ PyAudio installation may have issues" -ForegroundColor Yellow
    Write-Host "If voice recognition doesn't work, try:" -ForegroundColor Yellow
    Write-Host "  pip install pipwin" -ForegroundColor Cyan
    Write-Host "  pipwin install pyaudio" -ForegroundColor Cyan
}

# Create directories
Write-Host "`nCreating directories..." -ForegroundColor Yellow
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
    Write-Host "✓ Created data directory" -ForegroundColor Green
}

if (-not (Test-Path "models")) {
    New-Item -ItemType Directory -Path "models" | Out-Null
    Write-Host "✓ Created models directory" -ForegroundColor Green
    Write-Host "`n⚠ IMPORTANT: Download Vosk model and place in models\model\" -ForegroundColor Yellow
    Write-Host "Download from: https://alphacephei.com/vosk/models" -ForegroundColor Cyan
    Write-Host "Recommended: vosk-model-small-en-us-0.15" -ForegroundColor Cyan
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Download Vosk model from https://alphacephei.com/vosk/models" -ForegroundColor White
Write-Host "2. Extract to models\model\ directory" -ForegroundColor White
Write-Host "3. Run: .\run.ps1" -ForegroundColor White
Write-Host ""
