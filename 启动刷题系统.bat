@echo off
chcp 65001 >nul
cd /d "%~dp0exam-app"
python server.py
pause
