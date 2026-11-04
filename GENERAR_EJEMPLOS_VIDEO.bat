@echo off
cd /d "%~dp0"
title TecnoGUIA - generando ejemplos para el video (no cerrar)
.venv\Scripts\python.exe generar_ejemplos_video.py
echo.
pause
