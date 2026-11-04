@echo off
REM Crea el primer administrador de TecnoGUIA (solo si todavia no existe).
cd /d "%~dp0"
title TecnoGUIA - crear administrador
.venv\Scripts\python.exe crear_admin.py
echo.
pause
