@echo off
REM Inicia TecnoGUIA y abre la pantalla de ingreso.
cd /d "%~dp0"
title TecnoGUIA - servidor (no cerrar esta ventana)
echo Iniciando TecnoGUIA... Para detenerlo, cerra esta ventana o presiona Ctrl+C.
start "" cmd /c "timeout /t 5 >NUL & start http://127.0.0.1:8000/ingresar"
.venv\Scripts\python.exe -m uvicorn main:app --reload
echo.
echo El servidor se detuvo. Si aparece un error arriba, sacale una captura.
pause
