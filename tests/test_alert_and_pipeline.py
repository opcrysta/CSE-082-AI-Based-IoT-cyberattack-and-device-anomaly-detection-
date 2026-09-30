"""
Automated Pytest for Milestone 7: Pipeline Integration & Alert Engine.
Tests rule-based threat attribution, cyberattack vs hardware fault differentiation,
and live end-to-end MQTT telemetry -> inference -> alert publishing.
"""

import json
import time
import pytest
import paho.mqtt.client as mqtt
from alerts.alert_engine import AlertEngine, AlertEvent
from collector.mqtt_collector import MQTTCollectorService
from config.settings import mqtt_config


def test_alert_engine_dos_attribution():
    telemetry = {
        "device_id": "device_001",
        "temperature": 26.0,
        "voltage": 230.0,
        "cpu_usage": 92.0,
        "ram_usage": 45.0,
        "message_rate": 35.0,
        "failed_auth_count": 0,
        "network_latency": 45.0
    }
    ml_result = {"is_anomaly": True, "risk_score": 0.88, "raw_score": -0.11}

    alert = AlertEngine.evaluate(telemetry, ml_result)
    assert alert is not None
    assert alert.is_cyberattack is True
    assert alert.alert_category == "CYBERATTACK"
    assert "DoS" in alert.threat_name
    assert alert.severity == "CRITICAL"


def test_alert_engine_brute_force_attribution():
    telemetry = {
        "device_id": "device_002",
        "temperature": 25.0,
        "voltage": 230.0,
        "cpu_usage": 35.0,
        "ram_usage": 40.0,
        "message_rate": 1.0,
        "failed_auth_count": 12,
        "network_latency": 15.0
    }
    ml_result = {"is_anomaly": True, "risk_score": 0.75, "raw_score": -0.06}

    alert = AlertEngine.evaluate(telemetry, ml_result)
    assert alert is not None
    assert alert.is_cyberattack is True
    assert alert.alert_category == "CYBERATTACK"
    assert "Brute-Force" in alert.threat_name


def test_alert_engine_hardware_voltage_surge_attribution():
    telemetry = {
        "device_id": "device_003",
        "temperature": 25.0,
        "voltage": 295.0,  # Surge
        "cpu_usage": 15.0,
        "ram_usage": 40.0,
        "message_rate": 1.0,
        "failed_auth_count": 0,
        "network_latency": 15.0
    }
    ml_result = {"is_anomaly": True, "risk_score": 0.80, "raw_score": -0.09}

    alert = AlertEngine.evaluate(telemetry, ml_result)
    assert alert is not None
    assert alert.is_cyberattack is False  # Must NOT be flagged as cyberattack
    assert alert.alert_category == "HARDWARE_FAULT"
    assert "Voltage" in alert.threat_name


def test_alert_engine_normal_telemetry_returns_none():
    telemetry = {
        "device_id": "device_001",
        "temperature": 25.0,
        "voltage": 230.0,
        "cpu_usage": 15.0,
        "ram_usage": 40.0,
        "message_rate": 1.0,
        "failed_auth_count": 0,
        "network_latency": 15.0
    }
    ml_result = {"is_anomaly": False, "risk_score": 0.05, "raw_score": 0.15}

    alert = AlertEngine.evaluate(telemetry, ml_result)
    assert alert is None


def test_end_to_end_mqtt_collector_alert_pipeline():
    """
    Spins up the collector service, publishes telemetry,
    and asserts that alerts are properly published to iot/alerts on Mosquitto.
    """
    # 1. Start Collector in non-blocking background loop
    collector = MQTTCollectorService()
    collector.client.connect(mqtt_config.broker_host, mqtt_config.broker_port, keepalive=10)
    collector.client.loop_start()

    # 2. Setup an Alert Listener subscribed to iot/alerts
    received_alerts = []

    def on_alert_msg(client, userdata, message):
        alert_payload = json.loads(message.payload.decode("utf-8"))
        received_alerts.append(alert_payload)

    listener = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="pytest_alert_listener"
    )
    listener.on_message = on_alert_msg
    listener.connect(mqtt_config.broker_host, mqtt_config.broker_port, keepalive=10)
    listener.subscribe(mqtt_config.alert_topic, qos=0)
    listener.loop_start()

    time.sleep(0.5)  # Allow subscriptions to register

    # 3. Setup Test Publisher
    publisher = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="pytest_pipeline_publisher"
    )
    publisher.connect(mqtt_config.broker_host, mqtt_config.broker_port, keepalive=10)
    publisher.loop_start()

    try:
        # A. Publish Normal Telemetry
        normal_pkt = {
            "device_id": "test_normal_dev",
            "temperature": 25.0,
            "voltage": 230.0,
            "cpu_usage": 15.0,
            "ram_usage": 40.0,
            "message_rate": 1.0,
            "failed_auth_count": 0,
            "network_latency": 15.0
        }
        publisher.publish("iot/devices/test_normal_dev/telemetry", json.dumps(normal_pkt), qos=0)
        time.sleep(1.0)
        assert len(received_alerts) == 0, "Normal telemetry must NOT produce an alert"

        # B. Publish DoS Flood Attack Telemetry
        dos_attack_pkt = {
            "device_id": "test_attack_dev",
            "temperature": 26.0,
            "voltage": 230.0,
            "cpu_usage": 95.0,
            "ram_usage": 42.0,
            "message_rate": 45.0,
            "failed_auth_count": 0,
            "network_latency": 50.0
        }
        publisher.publish("iot/devices/test_attack_dev/telemetry", json.dumps(dos_attack_pkt), qos=0)

        # Wait up to 3 seconds for alert delivery
        timeout = 3.0
        start = time.time()
        while not received_alerts and (time.time() - start) < timeout:
            time.sleep(0.1)

        # Assertions on received alert
        assert len(received_alerts) == 1, "Attack telemetry must trigger exactly 1 alert"
        delivered_alert = received_alerts[0]
        assert delivered_alert["device_id"] == "test_attack_dev"
        assert delivered_alert["is_cyberattack"] is True
        assert delivered_alert["alert_category"] == "CYBERATTACK"
        assert delivered_alert["severity"] == "CRITICAL"
        assert "DoS" in delivered_alert["threat_name"]

    finally:
        publisher.loop_stop()
        publisher.disconnect()
        listener.loop_stop()
        listener.disconnect()
        collector.client.loop_stop()
        collector.client.disconnect()
