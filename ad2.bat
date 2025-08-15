@echo off
title ACARSDECO2 + ACARS Bridge + Mapa
cd /d "%~dp0"

REM Inicia o acarsdeco2.exe
start "ACARSDECO2" acarsdeco2.exe --device-serial 1 --gain 39.0 --freq 131550000 --freq 131825000 --logfile log --http-port 8091

REM Aguarda 3 segundos para gerar log
timeout /t 3 /nobreak >nul

REM Inicia o acars_bridge.py
start "ACARS Bridge" python acars_bridge.py

REM Aguarda 5 segundos
timeout /t 5 /nobreak >nul

REM Abre no Chrome o mapa
start "" "chrome.exe" "http://127.0.0.1:5000"

pause
