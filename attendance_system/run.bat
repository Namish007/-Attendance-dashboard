@echo off
:: ─────────────────────────────────────────────────────────────
:: run.bat  —  Windows one-click launcher
:: Double-click this file OR run it in CMD from the project root.
:: ─────────────────────────────────────────────────────────────

title AI Smart Attendance System

echo.
echo =====================================================
echo   AI-Based Smart Attendance System — NIET
echo =====================================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.10+ from python.org
    pause & exit /b 1
)

:: Check if dependencies are installed (quick check)
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Dependency installation failed.
        pause & exit /b 1
    )
)

:: Check if encodings exist
if not exist "models\encodings.pkl" (
    echo [WARN] Face encodings not found.
    echo        Run training first? (y/n)
    set /p choice="> "
    if /i "%choice%"=="y" (
        echo [INFO] Training face model...
        python backend\utils\train_faces.py
    )
)

echo.
echo [INFO] Starting Flask server...
echo [INFO] Open your browser at: http://localhost:5000
echo [INFO] Press Ctrl+C to stop the server.
echo.

python backend\app.py

pause
