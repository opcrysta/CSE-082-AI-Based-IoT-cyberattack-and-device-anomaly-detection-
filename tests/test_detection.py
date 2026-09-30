"""
Automated Pytest for Milestone 6: Isolation Forest Model & Inference.
Tests model persistence, inference accuracy on normal telemetry,
and detection sensitivity on distinct cyberattack scenarios.
"""

import pytest
import numpy as np
from detection.predict import AnomalyDetector
from config.settings import model_config


@pytest.fixture(scope="module")
def detector():
    return AnomalyDetector(model_config.model_path)


def test_model_artifact_integrity(detector):
    assert detector.artifact is not None
    assert "model" in detector.artifact
    assert "feature_names" in detector.artifact
    assert detector.feature_names == list(model_config.feature_columns)
    assert detector.artifact["contamination"] == model_config.contamination


def test_normal_telemetry_inference(detector):
    normal_reading = {
        "device_id": "device_001",
        "temperature": 25.0,
        "voltage": 230.0,
        "cpu_usage": 15.0,
        "ram_usage": 40.0,
        "message_rate": 1.0,
        "failed_auth_count": 0,
        "network_latency": 15.0
    }
    result = detector.predict_telemetry(normal_reading)

    assert result["prediction"] == 1, "Normal reading must be classified as inlier (1)"
    assert result["is_anomaly"] is False
    assert result["raw_score"] > 0.0, "Normal reading should have a positive decision function score"
    assert result["risk_score"] < 0.40, "Normal reading should have a low calibrated risk score"


def test_dos_attack_inference(detector):
    dos_reading = {
        "device_id": "device_001",
        "temperature": 26.5,
        "voltage": 230.0,
        "cpu_usage": 95.0,     # Extreme CPU spike
        "ram_usage": 42.0,
        "message_rate": 40.0,   # 40x normal message rate
        "failed_auth_count": 0,
        "network_latency": 45.0
    }
    result = detector.predict_telemetry(dos_reading)

    assert result["prediction"] == -1, "DoS flood must be detected as anomaly (-1)"
    assert result["is_anomaly"] is True
    assert result["raw_score"] < 0.0
    assert result["risk_score"] > 0.70, "DoS flood must produce high risk score"


def test_brute_force_attack_inference(detector):
    brute_force_reading = {
        "device_id": "device_002",
        "temperature": 25.0,
        "voltage": 230.0,
        "cpu_usage": 35.0,
        "ram_usage": 40.0,
        "message_rate": 1.0,
        "failed_auth_count": 20,  # 20 failed logins vs 0 normal
        "network_latency": 15.0
    }
    result = detector.predict_telemetry(brute_force_reading)

    assert result["prediction"] == -1
    assert result["is_anomaly"] is True
    assert result["risk_score"] > 0.65


def test_sensor_tampering_inference(detector):
    tampered_reading = {
        "device_id": "device_003",
        "temperature": 88.0,    # Overheating spike
        "voltage": 310.0,       # Severe overvoltage surge
        "cpu_usage": 15.0,
        "ram_usage": 40.0,
        "message_rate": 1.0,
        "failed_auth_count": 0,
        "network_latency": 15.0
    }
    result = detector.predict_telemetry(tampered_reading)

    assert result["prediction"] == -1
    assert result["is_anomaly"] is True


def test_risk_score_calibration_bounds(detector):
    for raw in [-1.0, -0.5, -0.1, 0.0, 0.1, 0.5, 1.0]:
        risk = detector.calculate_risk_score(raw)
        assert 0.0 <= risk <= 1.0
