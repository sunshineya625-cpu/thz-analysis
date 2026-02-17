@echo off
title THz Analysis Studio v3.0
color 0A
echo.
echo  ================================================
echo    THz Spectroscopy Analysis Studio  v3.0
echo    Publication-quality · Science/Nature standard
echo  ================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause & exit /b 1
)

if not exist "venv" (
    echo [SETUP] Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat

echo [SETUP] Checking dependencies...
pip install -q -r requirements.txt

echo.
echo  Ready! Opening browser at:
echo    Local:   http://localhost:8501
echo    Network: shown below (share with supervisor / 发给导师)
echo.
echo  Press Ctrl+C to stop / 按 Ctrl+C 停止
echo.

streamlit run app.py --server.address 0.0.0.0

pause
