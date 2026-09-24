@echo off
title StockAI Platform Server
echo ====================================================
echo  StockAI - AI-Powered Stock Analysis Platform
echo ====================================================
echo.
echo Starting server on http://localhost:8000 ...
echo.
py main.py
if %ERRORLEVEL% NEQ 0 (
    python main.py
)
pause
