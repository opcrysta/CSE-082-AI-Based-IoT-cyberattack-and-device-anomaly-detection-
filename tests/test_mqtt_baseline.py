"""
Automated Pytest for Milestone 2: MQTT Pub/Sub Baseline.
Tests that a published JSON message on 'iot/devices/{device_id}/telemetry'
is correctly received and decoded by a wildcard subscriber ('iot/devices/+/telemetry').
"""

import json
import time
import pytest
import paho.mqtt.client as mqtt
from config.settings import mqtt_config


def test_mqtt_publish_subscribe_json():
    received_messages = []

    # 1. Setup Subscriber
    subscriber = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="pytest_subscriber"
    )

    def on_message(client, userdata, message):
        payload_data = json.loads(message.payload.decode("utf-8"))
        received_messages.append((message.topic, payload_data))

    subscriber.on_message = on_message
    subscriber.connect(mqtt_config.broker_host, mqtt_config.broker_port, keepalive=10)
    subscriber.subscribe(mqtt_config.telemetry_topic_pattern, qos=0)
    subscriber.loop_start()

    time.sleep(0.5)  # Allow subscriber connection & subscription to register

    # 2. Setup Publisher and Send Telemetry
    publisher = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="pytest_publisher"
    )
    publisher.connect(mqtt_config.broker_host, mqtt_config.broker_port, keepalive=10)
    publisher.loop_start()

    test_payload = {
        "device_id": "test_device_999",
        "temperature": 27.5,
        "voltage": 231.0,
        "cpu_usage": 12.3,
        "ram_usage": 35.8,
        "message_rate": 1.0,
        "failed_auth_count": 0,
        "network_latency": 10.5
    }

    target_topic = "iot/devices/test_device_999/telemetry"
    publisher.publish(target_topic, json.dumps(test_payload), qos=0)

    # 3. Wait up to 3 seconds for message delivery
    timeout = 3.0
    start_time = time.time()
    while not received_messages and (time.time() - start_time) < timeout:
        time.sleep(0.1)

    # 4. Cleanup connections
    subscriber.loop_stop()
    subscriber.disconnect()
    publisher.loop_stop()
    publisher.disconnect()

    # 5. Assertions (filter for target test device topic)
    target_messages = [m for m in received_messages if m[0] == target_topic]
    assert len(target_messages) >= 1, "Failed to receive message over MQTT broker!"
    recv_topic, recv_data = target_messages[0]
    assert recv_topic == target_topic
    assert recv_data["device_id"] == "test_device_999"
    assert recv_data["temperature"] == 27.5
    assert recv_data["voltage"] == 231.0
