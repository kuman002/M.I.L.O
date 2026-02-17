# MILO - PowerShell Run Script
# Managing Information & Lifestyle Optimizer

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MILO - Managing Information & Lifestyle Optimizer" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

# Check if dependencies are installed
Write-Host "`nChecking dependencies..." -ForegroundColor Yellow
$deps = @("PyQt5", "pyttsx3", "vosk", "pyaudio")
$missingDeps = @()

foreach ($dep in $deps) {
    $result = python -c "import $dep" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ $dep installed" -ForegroundColor Green
    } else {
        Write-Host "✗ $dep not found" -ForegroundColor Red
        $missingDeps += $dep
    }
}

if ($missingDeps.Count -gt 0) {
    Write-Host "`nMissing dependencies detected!" -ForegroundColor Yellow
    Write-Host "Install them using: pip install -r requirements.txt" -ForegroundColor Yellow
    $install = Read-Host "Would you like to install now? (Y/N)"
    if ($install -eq "Y" -or $install -eq "y") {
        Write-Host "Installing dependencies..." -ForegroundColor Yellow
        pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Installation failed. Please install manually." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Please install dependencies before running MILO." -ForegroundColor Red
        exit 1
    }
}

# Check for Vosk model
Write-Host "`nChecking Vosk model..." -ForegroundColor Yellow
if (Test-Path "models\model") {
    Write-Host "✓ Vosk model found" -ForegroundColor Green
} else {
    Write-Host "⚠ Vosk model not found at models\model\" -ForegroundColor Yellow
    Write-Host "Voice recognition will be disabled." -ForegroundColor Yellow
    Write-Host "Download from: https://alphacephei.com/vosk/models" -ForegroundColor Cyan
}

# Create data directory if it doesn't exist
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
    Write-Host "✓ Created data directory" -ForegroundColor Green
}

# Run the application
Write-Host "`nStarting MILO..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

python src\main.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nApplication exited with errors." -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
