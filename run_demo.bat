@echo off
REM Quick demo script for Emergency Building Sweep Simulator (Windows)

echo ============================================================
echo   Emergency Building Sweep Simulator - Quick Demo
echo   HiMCM 2025 MVP
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Check dependencies
echo Checking dependencies...
python -c "import numpy, matplotlib, pandas, networkx" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)
echo [OK] All dependencies installed
echo.

REM Run tests
echo Running acceptance tests...
python test_acceptance.py
if errorlevel 1 (
    echo Error: Tests failed
    pause
    exit /b 1
)
echo.

REM Run demo
echo ============================================================
echo   Running Demo Simulation
echo ============================================================
echo.
echo Scenario: Simple office (1 floor, 1 agent, no hazards)
echo Running in headless mode for speed...
echo.

python main.py --no-viz --scenario simple

echo.
echo ============================================================
echo   Demo Complete!
echo ============================================================
echo.
echo Next steps:
echo   1. View results in the outputs\ directory
echo   2. Run with visualization: python main.py
echo   3. Try other scenarios: python main.py --scenario office
echo   4. See USAGE.md for more options
echo.
pause

