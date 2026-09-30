"""
Basic MQTT Publisher (Simulator Test)
Sends a sample JSON telemetry payload to iot/devices/device_001/telemetry.
"""

import json
import time
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import paho.mqtt.client as mqtt
from config.settings import mqtt_config


def publish_sample_telemetry():
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="test_device_publisher"
    )

    try:
        print(f"[INFO] Connecting to broker at {mqtt_config.broker_host}:{mqtt_config.broker_port}...")
        client.connect(mqtt_config.broker_host, mqtt_config.broker_port, keepalive=mqtt_config.keep_alive)
        client.loop_start()
        time.sleep(0.5)

        device_id = "device_001"
        target_topic = f"iot/devices/{device_id}/telemetry"

        telemetry_payload = {
            "device_id": device_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature": 25.4,
            "voltage": 230.1,
            "cpu_usage": 15.6,
            "ram_usage": 44.2,
            "message_rate": 1.0,
            "failed_auth_count": 0,
            "network_latency": 14.8
        }

        json_payload = json.dumps(telemetry_payload, indent=2)
        print(f"[INFO] Publishing payload to topic '{target_topic}':")
        print(json_payload)

        result = client.publish(target_topic, json_payload, qos=0)
        result.wait_for_publish()

        if result.is_published():
            print("\n[SUCCESS] Telemetry message successfully published!")
        else:
            print("\n[ERROR] Message failed to publish.")

        time.sleep(0.5)

    except ConnectionRefusedError:
        print(f"[ERROR] Could not connect to {mqtt_config.broker_host}:{mqtt_config.broker_port}.")
    finally:
        client.loop_stop()
        client.disconnect()
        print("[INFO] Publisher disconnected.")


if __name__ == "__main__":
    publish_sample_telemetry()
