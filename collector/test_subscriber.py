"""
Basic MQTT Subscriber (Collector Test)
Subscribes to all device telemetry topics and parses JSON messages.
"""

import json
import sys
from pathlib import Path

# Add project root to sys.path so config imports work reliably
sys.path.append(str(Path(__file__).resolve().parent.parent))

import paho.mqtt.client as mqtt
from config.settings import mqtt_config


def on_connect(client, userdata, flags, reason_code, properties=None):
    """Callback triggered when client connects to Mosquitto."""
    if reason_code == 0:
        print(f"[SUCCESS] Connected to Mosquitto Broker at {mqtt_config.broker_host}:{mqtt_config.broker_port}")
        client.subscribe(mqtt_config.telemetry_topic_pattern, qos=0)
        print(f"[INFO] Subscribed to topic pattern: '{mqtt_config.telemetry_topic_pattern}'")
        print("[INFO] Waiting for incoming telemetry messages... (Press Ctrl+C to stop)\n")
    else:
        print(f"[ERROR] Connection failed with reason code: {reason_code}")


def on_message(client, userdata, message):
    """Callback triggered whenever a message arrives on a subscribed topic."""
    topic = message.topic
    raw_payload = message.payload.decode("utf-8")

    try:
        data = json.loads(raw_payload)
        device_id = data.get("device_id", "UNKNOWN")
        temp = data.get("temperature", 0.0)
        volt = data.get("voltage", 0.0)
        cpu = data.get("cpu_usage", 0.0)
        rate = data.get("message_rate", 0.0)

        print(
            f"[TELEMETRY RECEIVED] Topic: {topic}\n"
            f"   -> Device: {device_id} | Temp: {temp:.1f}°C | Voltage: {volt:.1f}V | "
            f"CPU: {cpu:.1f}% | MsgRate: {rate:.1f} msg/s\n"
        )
    except json.JSONDecodeError as err:
        print(f"[WARNING] Non-JSON payload received on {topic}: {raw_payload} (Error: {err})")


def start_subscriber():
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="test_collector_subscriber"
    )

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        print(f"[INFO] Connecting to {mqtt_config.broker_host}:{mqtt_config.broker_port}...")
        client.connect(mqtt_config.broker_host, mqtt_config.broker_port, keepalive=mqtt_config.keep_alive)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Gracefully shutting down subscriber...")
    except ConnectionRefusedError:
        print(f"[ERROR] Could not connect to Mosquitto at {mqtt_config.broker_host}:{mqtt_config.broker_port}.")
    finally:
        client.disconnect()
        print("[INFO] Disconnected from broker.")


if __name__ == "__main__":
    start_subscriber()
