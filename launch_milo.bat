@echo off
REM MILO - Managing Information & Lifestyle Optimizer
REM Launcher script with conda environment activation

echo ========================================
echo   MILO - Voice-Controlled Dashboard
echo ========================================
echo.

REM Activate conda environment
call conda activate milo_stable

REM Check if activation was successful
if errorlevel 1 (
    echo Error: Could not activate conda environment
    echo Make sure you have conda installed and 'milo_stable' environment exists
    pause
    exit /b 1
)

echo Starting MILO with GPU-accelerated voice recognition...
echo.

REM Run the application
python src\main.py

REM If the app exits, pause to show any error messages
pause
