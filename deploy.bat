@echo off
setlocal enabledelayedexpansion
title Deploy IoT Security Stack - Production

echo ======================================================================
echo    AI-Based IoT Cyberattack ^& Anomaly Detection
echo    Unified Production Stack Deployment
echo ======================================================================
echo.

REM 1. Verify Docker Availability
where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH.
    echo Please install Docker Desktop and start the Docker daemon first.
    pause
    exit /b 1
)

REM 2. Check if Docker daemon is running
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker daemon is not running.
    echo Please launch Docker Desktop and wait until it is fully ready.
    pause
    exit /b 1
)

echo [*] Docker daemon detected and responsive.
echo [*] Building and deploying unified multi-container production stack...
echo.

REM 3. Deploy all 4 containers with build
docker compose up -d --build

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Docker Compose deployment encountered an error.
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo    DEPLOYMENT SUCCESSFUL! ALL SERVICES OPERATIONAL
echo ======================================================================
echo.
echo [*] Service Endpoints:
echo     - Grafana Executive SOC Dashboard:  http://localhost:3000/d/iot-security-overview
echo       Credentials:                      admin / admin
echo.
echo     - InfluxDB Time-Series Explorer:    http://localhost:8086
echo       Credentials:                      admin / adminpassword123
echo       Organization / Bucket:            iot_security_org / iot_telemetry
echo.
echo     - Mosquitto MQTT Broker:            localhost:1883
echo       Telemetry Pattern:                iot/devices/+/telemetry
echo       Alert Feed:                       iot/alerts
echo.
echo     - AI Detection ^& Streaming Engine: Container "iot_pipeline" (Active)
echo.
echo [*] Useful Commands:
echo     - View real-time pipeline logs:     docker logs -f iot_pipeline
echo     - Stop deployment:                  docker compose down
echo.
pause
