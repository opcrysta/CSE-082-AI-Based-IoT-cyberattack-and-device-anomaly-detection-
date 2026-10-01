@echo off
title IoT Security Pipeline Demo
echo ======================================================================
echo    Running IoT Cyberattack ^& Anomaly Detection - Turnkey Demo
echo ======================================================================
echo.

REM 1. Ensure Docker containers are running
echo [*] Starting InfluxDB and Grafana containers...
docker compose -f docker/docker-compose.yml up -d

echo.
echo [*] Running turnkey demonstration...
echo.
.\venv\Scripts\python.exe run_pipeline_demo.py
pause
