"""
Turnkey End-to-End Live Demonstration Runner.
Project P_310: AI-Based IoT Cyberattack and Device Anomaly Detection.

Orchestrates the entire live architecture in a single command:
1. Health-checks infrastructure (Mosquitto 1883, InfluxDB 8086, Grafana 3000).
2. Spawns the central MQTT Collector & Anomaly Detection pipeline in background.
3. Emits Normal Baseline IoT Telemetry across 3 devices.
4. Injects Live Controlled Cyberattacks (DoS, Brute-Force Auth) and Hardware Faults (Voltage Surge).
5. Verifies InfluxDB persistence and displays Grafana dashboard coordinates.
"""

import sys
import time
import socket
import threading
import json
from pathlib import Path
from typing import Dict, Any, List

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

import paho.mqtt.client as mqtt
from config.settings import mqtt_config, influx_config, model_config
from collector.mqtt_collector import MQTTCollectorService
from storage.database import InfluxDBService
from simulator.device_simulator import IoTDevice
from simulator.attack_scenarios import AttackScenarioGenerator


def check_port(host: str, port: int, service_name: str) -> bool:
    """Checks if a TCP port is open and listening."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1.5)
    try:
        sock.connect((host, port))
        sock.close()
        print(f"  [OK] {service_name:<18} is listening on {host}:{port}")
        return True
    except Exception:
        print(f"  [WARN] {service_name:<18} is NOT responding on {host}:{port}")
        return False


def run_pipeline_demo(auto_exit: bool = False):
    print("=" * 78)
    print("   AI-BASED IOT CYBERATTACK & DEVICE ANOMALY DETECTION - LIVE DEMO RUNNER   ")
    print("=" * 78)

    # 1. Environment & Service Pre-Checks
    print("\n[STEP 1/5] Verifying Infrastructure Services...")
    mosq_ok = check_port(mqtt_config.broker_host, mqtt_config.broker_port, "Mosquitto Broker")
    influx_ok = check_port("localhost", 8086, "InfluxDB Time-Series")
    grafana_ok = check_port("localhost", 3000, "Grafana Dashboards")

    model_file = model_config.model_path
    if model_file.exists():
        print(f"  [OK] Model Artifact     found at: {model_file.name}")
    else:
        print(f"  [FAIL] Model Artifact   MISSING at: {model_file}")
        sys.exit(1)

    if not mosq_ok:
        print("\n[ERROR] Mosquitto MQTT Broker is not running. Please start Mosquitto on port 1883.")
        sys.exit(1)

    # 2. Start Central Collector Service in Background Thread
    print("\n[STEP 2/5] Initializing Real-Time Collector & Isolation Forest Pipeline...")
    collector = MQTTCollectorService()
    collector_thread = threading.Thread(target=collector.start, daemon=True)
    collector_thread.start()
    time.sleep(1.0)  # Allow MQTT connection & topic subscription

    # Setup demo publisher
    pub_client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="demo_traffic_generator"
    )
    pub_client.connect(mqtt_config.broker_host, mqtt_config.broker_port, keepalive=30)
    pub_client.loop_start()

    try:
        # 3. Normal Telemetry Generation
        print("\n[STEP 3/5] Simulating Normal Baseline Telemetry (3 Cycles)...")
        normal_devices = [
            IoTDevice(device_id="device_001"),
            IoTDevice(device_id="device_002"),
            IoTDevice(device_id="device_003"),
        ]

        for cycle in range(1, 4):
            print(f"\n--- Normal Emission Cycle {cycle}/3 ---")
            for dev in normal_devices:
                telemetry = dev.generate_normal_telemetry()
                topic = f"iot/devices/{dev.device_id}/telemetry"
                pub_client.publish(topic, json.dumps(telemetry), qos=0)
                time.sleep(0.3)
            time.sleep(0.5)

        time.sleep(1.0)

        # 4. Live Attack Scenarios & Attribution
        print("\n" + "=" * 78)
        print("[STEP 4/5] INJECTING CONTROLLED THREAT SCENARIOS & THREAT ATTRIBUTION")
        print("=" * 78)

        attack_gen = AttackScenarioGenerator()

        # Attack 1: DoS Flooding on device_001
        print("\n>>> Scenario A: DoS Flooding Attack on device_001")
        print("    [Injecting]: 15 high-frequency packets, message_rate=35.0 msg/s, cpu_usage=88.5%")
        for i in range(15):
            dos_sample = attack_gen.generate_dos_flooding("device_001")
            pub_client.publish("iot/devices/device_001/telemetry", json.dumps(dos_sample), qos=0)
            time.sleep(0.08)

        time.sleep(1.0)

        # Attack 2: Brute-Force Credential Attack on device_002
        print("\n>>> Scenario B: Brute-Force Authentication Attempt on device_002")
        print("    [Injecting]: Burst of repeated unauthorized login attempts (failed_auth_count=18)")
        for i in range(5):
            auth_sample = attack_gen.generate_brute_force_auth("device_002")
            pub_client.publish("iot/devices/device_002/telemetry", json.dumps(auth_sample), qos=0)
            time.sleep(0.15)

        time.sleep(1.0)

        # Attack 3: Physical Voltage Surge on device_003
        print("\n>>> Scenario C: Physical Electrical Voltage Surge on device_003")
        print("    [Injecting]: Overvoltage spike (voltage=268.5V, zero failed authentications)")
        for i in range(3):
            surge_sample = attack_gen.generate_sensor_tampering("device_003")
            pub_client.publish("iot/devices/device_003/telemetry", json.dumps(surge_sample), qos=0)
            time.sleep(0.2)

        time.sleep(1.5)

        # 5. Database Persistence & Grafana Summary
        print("\n" + "=" * 78)
        print("[STEP 5/5] VERIFYING PERSISTENCE & MONITORING ACCESS")
        print("=" * 78)
        print(f"  Collector Packets Processed: {collector.total_processed}")
        print(f"  Anomalies Detected:        {collector.anomalies_detected}")
        print(f"  Alerts Dispatched:         {collector.alerts_published}")
        print(f"  Validation Rejections:     {collector.validation_errors}")

        # Check InfluxDB status
        if influx_ok and collector.db_service.is_online:
            print(f"\n  [DATABASE] Telemetry points securely written to InfluxDB (Bucket: '{influx_config.bucket}').")
        else:
            print("\n  [DATABASE] Offline SQLite Buffer active (Store-and-Forward mechanism).")

        # Load persisted evaluation metrics
        report_file = BASE_DIR / "models" / "evaluation_report.json"
        if report_file.exists():
            with open(report_file, "r", encoding="utf-8") as f:
                rep = json.load(f)
            ton_m = rep.get("benchmarks", {}).get("ton_iot_benchmark", {}).get("metrics", {})
            syn_m = rep.get("benchmarks", {}).get("synthetic_scenarios", {}).get("metrics", {})
            print("\n  [OFFLINE BENCHMARK RECAP]")
            print(f"    Synthetic Scenarios : Precision = {syn_m.get('precision', 0)*100:.1f}% | Recall = {syn_m.get('recall', 0)*100:.1f}% | ROC-AUC = {syn_m.get('roc_auc', 0):.4f}")
            print(f"    UNSW TON_IoT Dataset: Precision = {ton_m.get('precision', 0)*100:.1f}% | Recall = {ton_m.get('recall', 0)*100:.1f}% | ROC-AUC = {ton_m.get('roc_auc', 0):.4f}")

        print("\n" + "*" * 78)
        print("  LIVE GRAFANA DASHBOARD COORDINATES:")
        print("  URL:         http://localhost:3000/d/iot-security-overview")
        print("  Credentials: admin / admin")
        print("  Panels:      Anomaly Risk Gauge | Telemetry Matrix | DoS Rates | Incident Audit Table")
        print("*" * 78)

        if not auto_exit:
            print("\n[INFO] End-to-end pipeline is actively listening for live telemetry.")
            print("[INFO] Press Ctrl+C anytime to gracefully stop the demonstration.\n")
            try:
                while True:
                    time.sleep(1.0)
            except KeyboardInterrupt:
                print("\n[INFO] Stopping live demonstration...")

    finally:
        pub_client.loop_stop()
        pub_client.disconnect()
        collector.stop()
        print("[DEMO COMPLETE] Thank you!\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="IoT Pipeline Live Demonstration Runner")
    parser.add_argument("--auto-exit", action="store_true", help="Exit automatically after attack injection sequence")
    args = parser.parse_args()

    run_pipeline_demo(auto_exit=args.auto_exit)
