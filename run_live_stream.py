"""
Continuous Live Telemetry Streamer & Dynamic Threat Injector.
Runs the complete real-time IoT security pipeline indefinitely:
1. Spawns MQTTCollectorService to process telemetry, score with Isolation Forest, and write to InfluxDB.
2. Continuously emits normal telemetry across 3 virtual devices (device_001, device_002, device_003).
3. Periodically (every ~45s) injects a controlled threat burst (DoS Flooding, Brute-Force, or Voltage Surge)
   to keep Grafana dashboards actively animating with realistic cyber defense activity.
"""

import sys
import time
import json
import threading
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

import paho.mqtt.client as mqtt
from config.settings import mqtt_config
from collector.mqtt_collector import MQTTCollectorService
from simulator.device_simulator import MultiDeviceSimulator
from simulator.attack_scenarios import AttackScenarioGenerator


def start_live_pipeline():
    print("=" * 78)
    print("      CONTINUOUS IOT LIVE STREAM & REAL-TIME ML DETECTION PIPELINE       ")
    print("=" * 78)
    print("[*] Starting Central Collector Service & InfluxDB writer...")

    collector = MQTTCollectorService()
    collector_thread = threading.Thread(target=collector.start, daemon=True)
    collector_thread.start()
    time.sleep(1.0)

    # Publisher client
    pub_client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="live_pipeline_streamer"
    )
    pub_client.connect(mqtt_config.broker_host, mqtt_config.broker_port, keepalive=60)
    pub_client.loop_start()

    simulator = MultiDeviceSimulator(num_devices=3, random_state=42)
    attack_gen = AttackScenarioGenerator(random_state=101)

    print("[*] Live telemetry streaming active across: device_001, device_002, device_003")
    print("[*] Grafana URL: http://localhost:3000/d/iot-security-overview (Auto-refreshing every 5s)")
    print("[*] Press Ctrl+C anytime to stop.\n")

    cycle_count = 0
    attack_types = ["dos", "brute_force", "voltage_surge"]
    attack_idx = 0

    try:
        while True:
            cycle_count += 1

            # Normal telemetry emission
            for device in simulator.devices:
                telemetry = device.generate_normal_telemetry()
                topic = f"iot/devices/{device.device_id}/telemetry"
                pub_client.publish(topic, json.dumps(telemetry), qos=0)

            # Every 60 cycles (~2 minutes), inject a brief controlled threat burst
            if cycle_count % 60 == 0:
                current_attack = attack_types[attack_idx % len(attack_types)]
                attack_idx += 1

                if current_attack == "dos":
                    print("\n" + "!" * 78)
                    print("[LIVE THREAT INJECTION] Launching DoS Flooding Attack on device_001...")
                    print("!" * 78)
                    for _ in range(8):
                        sample = attack_gen.generate_dos_flooding("device_001")
                        pub_client.publish("iot/devices/device_001/telemetry", json.dumps(sample), qos=0)
                        time.sleep(0.08)

                elif current_attack == "brute_force":
                    print("\n" + "!" * 78)
                    print("[LIVE THREAT INJECTION] Launching Brute-Force Auth Attack on device_002...")
                    print("!" * 78)
                    for _ in range(4):
                        sample = attack_gen.generate_brute_force_auth("device_002")
                        pub_client.publish("iot/devices/device_002/telemetry", json.dumps(sample), qos=0)
                        time.sleep(0.15)

                elif current_attack == "voltage_surge":
                    print("\n" + "!" * 78)
                    print("[LIVE FAULT INJECTION] Injecting Hardware Voltage Surge on device_003...")
                    print("!" * 78)
                    for _ in range(3):
                        sample = attack_gen.generate_sensor_tampering("device_003")
                        pub_client.publish("iot/devices/device_003/telemetry", json.dumps(sample), qos=0)
                        time.sleep(0.2)

            time.sleep(2.0)

    except KeyboardInterrupt:
        print("\n[INFO] Stopping live pipeline stream...")
    finally:
        pub_client.loop_stop()
        pub_client.disconnect()
        collector.stop()
        print("[INFO] Live stream terminated cleanly.")


if __name__ == "__main__":
    start_live_pipeline()
