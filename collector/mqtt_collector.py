"""
Central MQTT Telemetry Collector and Real-Time Detection Pipeline.
1. Subscribes to device telemetry topics: iot/devices/+/telemetry
2. Validates schema using Pydantic (DataValidator).
3. Extracts standardized feature vectors (FeatureExtractor).
4. Executes unsupervised inference via Isolation Forest (AnomalyDetector).
5. Triggers Threat Attribution & Alert Engine on anomalies (AlertEngine).
6. Publishes actionable alerts to MQTT topic: iot/alerts.
7. Dispatches events to time-series database (storage hook ready for Milestone 8).
"""

import json
import time
import sys
from pathlib import Path
from typing import Optional, Callable, Dict, Any

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import paho.mqtt.client as mqtt
from config.settings import mqtt_config
from collector.data_validator import DataValidator
from detection.predict import AnomalyDetector
from alerts.alert_engine import AlertEngine, AlertEvent
from storage.database import InfluxDBService


class MQTTCollectorService:
    """
    End-to-End Real-Time Collector and Anomaly Detection Service.
    """

    def __init__(
        self,
        db_service: Optional[InfluxDBService] = None,
        db_callback: Optional[Callable[[Dict[str, Any], Dict[str, Any], Optional[AlertEvent]], None]] = None
    ):
        self.detector = AnomalyDetector()
        self.db_service = db_service or InfluxDBService()
        self.db_callback = db_callback

        # Metrics counters
        self.total_processed = 0
        self.anomalies_detected = 0
        self.alerts_published = 0
        self.validation_errors = 0

        # Paho MQTT Client setup with Callback API Version 2
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id="central_iot_ml_collector"
        )
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            print(f"[COLLECTOR] Connected to Mosquitto at {mqtt_config.broker_host}:{mqtt_config.broker_port}")
            client.subscribe(mqtt_config.telemetry_topic_pattern, qos=0)
            print(f"[COLLECTOR] Subscribed to telemetry pattern: '{mqtt_config.telemetry_topic_pattern}'")
            print(f"[COLLECTOR] Alert publisher ready on topic: '{mqtt_config.alert_topic}'\n")
        else:
            print(f"[COLLECTOR ERROR] Connection failed with reason code: {reason_code}")

    def _on_message(self, client, userdata, message):
        self.total_processed += 1
        raw_payload = message.payload.decode("utf-8")
        topic = message.topic

        # Step 1: Schema Validation
        is_valid, payload, error_msg = DataValidator.validate_json_string(raw_payload)
        if not is_valid or payload is None:
            self.validation_errors += 1
            print(f"[COLLECTOR WARNING] Rejected invalid packet on {topic}: {error_msg}")
            return

        # Step 2: Real-Time Machine Learning Inference
        telemetry_dict = payload.model_dump()
        ml_result = self.detector.predict_telemetry(telemetry_dict)

        device_id = payload.device_id
        is_anomaly = ml_result["is_anomaly"]
        risk_score = ml_result["risk_score"]
        raw_score = ml_result["raw_score"]

        # Step 3: Threat Attribution & Alerting
        alert: Optional[AlertEvent] = None

        if is_anomaly or risk_score >= 0.50:
            self.anomalies_detected += 1
            alert = AlertEngine.evaluate(telemetry_dict, ml_result)

            if alert:
                self.alerts_published += 1
                alert_json = json.dumps(alert.to_dict())
                # Publish alert to iot/alerts topic
                self.client.publish(mqtt_config.alert_topic, alert_json, qos=0)

                tag = "[CYBERATTACK ALERT]" if alert.is_cyberattack else "[HARDWARE/ENV FAULT]"
                print(
                    f"{tag} Device: {device_id} | {alert.threat_name} | "
                    f"Severity: {alert.severity} | Risk: {risk_score:.3f} | Score: {raw_score:.3f}\n"
                    f"   Action: {alert.recommended_action}"
                )
        else:
            print(
                f"[COLLECTOR NORMAL] Device: {device_id} | "
                f"Temp: {payload.temperature:.1f} C | Volt: {payload.voltage:.1f}V | "
                f"CPU: {payload.cpu_usage:.1f}% | Risk: {risk_score:.3f}"
            )

        # Step 4: Time-Series Database Persistence (InfluxDB v2 + Local Buffer)
        try:
            self.db_service.write_telemetry(telemetry_dict, ml_result, alert)
        except Exception as e:
            print(f"[COLLECTOR WARNING] Database write error: {e}")

        if self.db_callback:
            try:
                self.db_callback(telemetry_dict, ml_result, alert)
            except Exception as e:
                print(f"[COLLECTOR ERROR] Custom callback failure: {e}")

    def start(self):
        """Starts the collector event loop."""
        try:
            print(f"[COLLECTOR] Initializing pipeline with Isolation Forest & InfluxDB...")
            self.client.connect(mqtt_config.broker_host, mqtt_config.broker_port, keepalive=mqtt_config.keep_alive)
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("\n[COLLECTOR] Stopping service...")
        except ConnectionRefusedError:
            print(f"[COLLECTOR ERROR] Could not connect to Mosquitto at {mqtt_config.broker_host}:{mqtt_config.broker_port}.")
        finally:
            self.stop()

    def stop(self):
        """Stops the collector service and prints summary statistics."""
        self.client.disconnect()
        if self.db_service:
            self.db_service.close()
        print(f"\n[COLLECTOR SHUTDOWN SUMMARY]")
        print(f"  Total Packets Processed: {self.total_processed}")
        print(f"  Anomalies Detected:      {self.anomalies_detected}")
        print(f"  Alerts Dispatched:       {self.alerts_published}")
        print(f"  Validation Errors:       {self.validation_errors}")


if __name__ == "__main__":
    service = MQTTCollectorService()
    service.start()
