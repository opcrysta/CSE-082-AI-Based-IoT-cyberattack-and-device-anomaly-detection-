@echo off
title IoT Security Live Pipeline
echo ======================================================================
echo    Starting IoT Cyberattack ^& Anomaly Detection Live System
echo ======================================================================
echo.

REM 1. Ensure Docker containers are running
echo [*] Starting InfluxDB and Grafana containers...
docker compose -f docker/docker-compose.yml up -d

echo.
echo [*] Dashboard URL: http://localhost:3000/d/iot-security-overview
echo [*] Login: admin / admin
echo.

REM 2. Run the live stream and detection pipeline
echo [*] Launching continuous live stream (Press Ctrl+C to stop)...
echo.
.\venv\Scripts\python.exe run_live_stream.py
pause
