#!/usr/bin/env bash
# ======================================================================
#  AI-Based IoT Cyberattack & Anomaly Detection
#  Linux / macOS / Cloud VPS Production Stack Deployment Script
# ======================================================================

set -euo pipefail

echo "======================================================================"
echo "   AI-Based IoT Cyberattack & Anomaly Detection"
echo "   Unified Production Stack Deployment"
echo "======================================================================"
echo ""

# 1. Verify Docker Availability
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed or not in PATH."
    echo "Please install Docker Engine: https://docs.docker.com/engine/install/"
    exit 1
fi

# 2. Check Docker daemon responsiveness
if ! docker info &> /dev/null; then
    echo "[ERROR] Docker daemon is not running."
    echo "Please start the Docker service (e.g., sudo systemctl start docker)."
    exit 1
fi

echo "[*] Docker daemon detected and responsive."
echo "[*] Building and deploying unified multi-container production stack..."
echo ""

# 3. Deploy all 4 containers with build
docker compose up -d --build

echo ""
echo "======================================================================"
echo "   DEPLOYMENT SUCCESSFUL! ALL SERVICES OPERATIONAL"
echo "======================================================================"
echo ""
echo "[*] Service Endpoints:"
echo "    - Grafana Executive SOC Dashboard:  http://localhost:3000/d/iot-security-overview"
echo "      Credentials:                      admin / admin"
echo ""
echo "    - InfluxDB Time-Series Explorer:    http://localhost:8086"
echo "      Credentials:                      admin / adminpassword123"
echo "      Organization / Bucket:            iot_security_org / iot_telemetry"
echo ""
echo "    - Mosquitto MQTT Broker:            localhost:1883"
echo "      Telemetry Pattern:                iot/devices/+/telemetry"
echo "      Alert Feed:                       iot/alerts"
echo ""
echo "    - AI Detection & Streaming Engine:  Container 'iot_pipeline' (Active)"
echo ""
echo "[*] Useful Commands:"
echo "    - View real-time pipeline logs:     docker logs -f iot_pipeline"
echo "    - Stop deployment:                  docker compose down"
echo "    - Restart stack:                    docker compose restart"
echo ""
