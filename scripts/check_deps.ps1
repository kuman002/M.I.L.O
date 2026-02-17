# Quick dependency checker for MILO

Write-Host "MILO Dependency Checker" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# Check Python
Write-Host "Python: " -NoNewline
try {
    $version = python --version 2>&1
    Write-Host $version -ForegroundColor Green
} catch {
    Write-Host "NOT FOUND" -ForegroundColor Red
    $allGood = $false
}

# Check each package
$packages = @{
    "PyQt5" = "PyQt5"
    "pyttsx3" = "pyttsx3"
    "vosk" = "vosk"
    "pyaudio" = "pyaudio"
    "python-dateutil" = "dateutil"
    "pandas" = "pandas"
}

Write-Host "`nPackages:" -ForegroundColor Yellow
foreach ($package in $packages.GetEnumerator()) {
    Write-Host "  $($package.Key): " -NoNewline
    $result = python -c "import $($package.Value)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Installed" -ForegroundColor Green
    } else {
        Write-Host "✗ Missing" -ForegroundColor Red
        $allGood = $false
    }
}

# Check Vosk model
Write-Host "`nVosk Model: " -NoNewline
if (Test-Path "models\model") {
    Write-Host "✓ Found" -ForegroundColor Green
} else {
    Write-Host "✗ Not Found" -ForegroundColor Yellow
    Write-Host "  (Voice recognition will be disabled)" -ForegroundColor Yellow
}

# Check data directory
Write-Host "`nData Directory: " -NoNewline
if (Test-Path "data") {
    Write-Host "✓ Exists" -ForegroundColor Green
} else {
    Write-Host "⚠ Will be created on first run" -ForegroundColor Yellow
}

Write-Host ""

if ($allGood) {
    Write-Host "✓ All dependencies are installed!" -ForegroundColor Green
    Write-Host "You can run MILO using: .\run.ps1" -ForegroundColor Cyan
} else {
    Write-Host "⚠ Some dependencies are missing." -ForegroundColor Yellow
    Write-Host "Run: .\setup.ps1 to install them" -ForegroundColor Cyan
}
