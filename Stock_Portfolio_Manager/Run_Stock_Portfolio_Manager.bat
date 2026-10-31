@echo off
setlocal enabledelayedexpansion

REM Set working directory to this script's directory
cd /d "%~dp0"
title Stock Portfolio Manager

REM Check for entry point
if not exist "app.py" (
    echo [ERROR] app.py was not found in "%~dp0".
    echo Please make sure this launcher is located in the Stock_Portfolio_Manager root directory.
    pause
    exit /b 1
)

REM Locate or determine Python interpreter
set "PYTHON_EXE="
if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=.venv\Scripts\python.exe"
if not defined PYTHON_EXE if exist "venv\Scripts\python.exe" set "PYTHON_EXE=venv\Scripts\python.exe"

if not defined PYTHON_EXE (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON_EXE=python"
)
if not defined PYTHON_EXE (
    where py >nul 2>nul
    if not errorlevel 1 set "PYTHON_EXE=py"
)

if not defined PYTHON_EXE (
    echo [ERROR] Python was not found on your system.
    echo Please install Python 3.10 or higher from https://www.python.org
    echo and ensure "Add Python to PATH" is checked during installation.
    pause
    exit /b 1
)

REM Check dependencies and install if missing
"%PYTHON_EXE%" -c "import ttkbootstrap, matplotlib" >nul 2>nul
if errorlevel 1 (
    echo [SETUP] Installing required dependencies (ttkbootstrap, matplotlib)...
    "%PYTHON_EXE%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies. Check your internet connection.
        pause
        exit /b 1
    )
)

echo Starting Stock Portfolio Manager...
"%PYTHON_EXE%" app.py
set "APP_EXIT_CODE=%ERRORLEVEL%"

if not "%APP_EXIT_CODE%"=="0" (
    echo.
    echo [ERROR] The application exited with code %APP_EXIT_CODE%.
    pause
)

exit /b %APP_EXIT_CODE%
