"""
Centralized Configuration Loader for IoT Anomaly Detection System.
Loads environment variables from .env file or system environment with typed fallbacks.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Base Project Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file from base directory
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class MQTTSettings:
    broker_host: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    broker_port: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    keep_alive: int = int(os.getenv("MQTT_KEEP_ALIVE", "60"))
    telemetry_topic_pattern: str = os.getenv("MQTT_TELEMETRY_TOPIC", "iot/devices/+/telemetry")
    alert_topic: str = os.getenv("MQTT_ALERT_TOPIC", "iot/alerts")


@dataclass(frozen=True)
class InfluxDBSettings:
    url: str = os.getenv("INFLUXDB_URL", "http://localhost:8086")
    token: str = os.getenv("INFLUXDB_TOKEN", "my-super-secret-iot-token-12345")
    org: str = os.getenv("INFLUXDB_ORG", "iot_security_org")
    bucket: str = os.getenv("INFLUXDB_BUCKET", "iot_telemetry")


@dataclass(frozen=True)
class ModelSettings:
    model_path: Path = BASE_DIR / os.getenv("MODEL_PATH", "models/isolation_forest.joblib")
    contamination: float = float(os.getenv("CONTAMINATION_RATE", "0.05"))
    random_state: int = int(os.getenv("RANDOM_STATE", "42"))
    
    # Feature ordering is strictly enforced across training and inference to avoid feature misalignment
    feature_columns: tuple = (
        "temperature",
        "voltage",
        "cpu_usage",
        "ram_usage",
        "message_rate",
        "failed_auth_count",
        "network_latency"
    )


@dataclass(frozen=True)
class SimulatorSettings:
    interval_sec: float = float(os.getenv("SIMULATION_INTERVAL_SEC", "2.0"))
    num_devices: int = int(os.getenv("NUM_DEVICES", "3"))


# Instantiate global configuration objects
mqtt_config = MQTTSettings()
influx_config = InfluxDBSettings()
model_config = ModelSettings()
sim_config = SimulatorSettings()
