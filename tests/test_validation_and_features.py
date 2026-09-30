"""
Automated Pytest for Milestone 5: Data Validation and Feature Extraction.
Tests Pydantic validation, malformed payload handling, feature vector formatting,
and TON_IoT real-world schema mapping.
"""

import json
import pytest
import numpy as np
import pandas as pd
from collector.data_validator import DataValidator, TelemetryPayload
from collector.feature_extractor import FeatureExtractor
from simulator.ton_iot_replay import TONIoTReplayEngine


def test_data_validator_valid_payload():
    valid_data = {
        "device_id": "device_001",
        "temperature": 25.5,
        "voltage": 230.2,
        "cpu_usage": 18.0,
        "ram_usage": 42.0,
        "message_rate": 1.0,
        "failed_auth_count": 0,
        "network_latency": 15.0
    }
    is_valid, payload, error = DataValidator.validate_dict(valid_data)
    assert is_valid is True
    assert error is None
    assert isinstance(payload, TelemetryPayload)
    assert payload.device_id == "device_001"
    assert payload.temperature == 25.5


def test_data_validator_malformed_json():
    is_valid, payload, error = DataValidator.validate_json_string("{invalid_json: true,}")
    assert is_valid is False
    assert payload is None
    assert "Malformed JSON" in error


def test_data_validator_missing_required_fields():
    # Temperature and device_id are strictly required
    incomplete_data = {
        "voltage": 230.0
    }
    is_valid, payload, error = DataValidator.validate_dict(incomplete_data)
    assert is_valid is False
    assert "device_id" in error or "temperature" in error


def test_data_validator_out_of_bounds_rejection():
    # Physical sensor constraint: temperature > 125.0 must be rejected
    unphysical_data = {
        "device_id": "device_001",
        "temperature": 999.0
    }
    is_valid, payload, error = DataValidator.validate_dict(unphysical_data)
    assert is_valid is False
    assert "temperature" in error


def test_feature_extractor_vector_shape_and_order():
    payload = TelemetryPayload(
        device_id="device_001",
        temperature=26.4,
        voltage=228.5,
        cpu_usage=14.0,
        ram_usage=45.0,
        message_rate=1.2,
        failed_auth_count=0,
        network_latency=12.5
    )

    vector = FeatureExtractor.extract_vector(payload)
    assert isinstance(vector, np.ndarray)
    assert vector.shape == (1, 7)

    # Check exact feature ordering matches:
    # ["temperature", "voltage", "cpu_usage", "ram_usage", "message_rate", "failed_auth_count", "network_latency"]
    expected = [26.4, 228.5, 14.0, 45.0, 1.2, 0.0, 12.5]
    np.testing.assert_allclose(vector[0], expected)


def test_ton_iot_row_mapping():
    sample_row = pd.Series({
        "date": "31-Mar-19",
        "time": "12:36:52",
        "current_temperature": 28.5,
        "thermostat_status": 1,
        "label": 1,
        "type": "password"
    })

    mapped = TONIoTReplayEngine.map_row_to_telemetry(sample_row)
    assert mapped["device_id"] == "ton_thermostat_001"
    assert mapped["temperature"] == 28.5
    assert mapped["is_anomaly"] == 1
    assert mapped["attack_type"] == "password"
    assert mapped["failed_auth_count"] >= 5, "Password attack must map to elevated failed auth"
