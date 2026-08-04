@echo off
setlocal enabledelayedexpansion

:: ============================================================================
::  Virtual Fence — Local Development Startup Script
::  Creates a Python virtual environment, installs dependencies, builds the
::  Next.js frontend, and launches the unified FastAPI server.
:: ============================================================================

title Virtual Fence — Startup

echo.
echo  ============================================================
echo     Virtual Fence
echo     Enterprise Autonomous Perimeter Intrusion ^& Spatial
echo     Boundary System
echo  ============================================================
echo.

:: ── Resolve project root (directory where this .bat lives) ──
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

:: ── Check Python is available ──
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python is not installed or not on PATH.
    echo          Download from https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
echo  [OK] Found %PY_VER%

:: ── Check Node.js is available ──
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Node.js is not installed or not on PATH.
    echo          Download from https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('node --version 2^>^&1') do set "NODE_VER=%%v"
echo  [OK] Found Node.js %NODE_VER%

:: ── Create / activate Python virtual environment ──
echo.
if not exist "venv\Scripts\activate.bat" (
    echo  [SETUP] Creating Python virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  [OK] Virtual environment created at venv\
) else (
    echo  [OK] Virtual environment already exists.
)

call venv\Scripts\activate.bat
echo  [OK] Virtual environment activated.

:: ── Install Python dependencies ──
echo.
echo  [SETUP] Installing Python dependencies...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to install Python dependencies.
    pause
    exit /b 1
)
echo  [OK] Python dependencies installed.

:: ── Create storage directories ──
if not exist "backend\storage\snapshots" (
    mkdir "backend\storage\snapshots"
    echo  [OK] Created storage directories.
)

:: ── Build frontend (if not already built) ──
echo.
if not exist "frontend\out\index.html" (
    echo  [SETUP] Building Next.js frontend - first run, may take a minute...
    cd frontend
    
    if not exist "node_modules" (
        echo         Installing npm packages...
        call npm install --silent
        if %errorlevel% neq 0 (
            echo  [ERROR] npm install failed.
            cd ..
            pause
            exit /b 1
        )
    )
    
    echo         Running build...
    call npm run build
    if %errorlevel% neq 0 (
        echo  [ERROR] Frontend build failed.
        cd ..
        pause
        exit /b 1
    )
    
    cd ..
    echo  [OK] Frontend built to frontend\out\
) else (
    echo  [OK] Frontend already built. Delete frontend\out to force rebuild.
)

:: ── Launch the server ──
echo.
echo  ============================================================
echo    All systems ready. Starting Virtual Fence...
echo  ============================================================
echo.
echo    Dashboard:   http://localhost:8000
echo    Video Feed:  http://localhost:8000/api/v1/video_feed
echo    API Docs:    http://localhost:8000/docs
echo.
echo    Press Ctrl+C to stop the server.
echo  ============================================================
echo.

set PYTHONPATH=%PROJECT_ROOT%
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

:: ── Cleanup on exit ──
echo.
echo  [INFO] Server stopped. Deactivating virtual environment.
call deactivate 2>nul
pause
