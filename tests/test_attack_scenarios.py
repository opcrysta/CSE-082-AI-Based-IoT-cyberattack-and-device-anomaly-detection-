"""
Automated Pytest for Milestone 4: Attack & Anomaly Scenarios.
Verifies that all 4 attack generators produce expected statistical deviations
and the labeled ground-truth evaluation dataset is formatted correctly.
"""

import pytest
import pandas as pd
from simulator.attack_scenarios import AttackScenarioGenerator


@pytest.fixture
def generator():
    return AttackScenarioGenerator(random_state=123)


def test_dos_flooding_characteristics(generator):
    for _ in range(50):
        data = generator.generate_dos_flooding("device_001")
        assert data["is_anomaly"] == 1
        assert data["attack_type"] == "dos_flooding"
        assert data["message_rate"] >= 15.0, "DoS flooding must exhibit abnormal message rate"
        assert data["cpu_usage"] >= 70.0, "DoS flooding must cause high CPU load"


def test_brute_force_auth_characteristics(generator):
    for _ in range(50):
        data = generator.generate_brute_force_auth("device_002")
        assert data["is_anomaly"] == 1
        assert data["attack_type"] == "brute_force_auth"
        assert data["failed_auth_count"] >= 5, "Brute force must exhibit repeated failed logins"


def test_sensor_tampering_characteristics(generator):
    for _ in range(50):
        data = generator.generate_sensor_tampering("device_003")
        assert data["is_anomaly"] == 1
        assert data["attack_type"] == "sensor_tampering"
        is_voltage_anomaly = (data["voltage"] > 260.0) or (data["voltage"] < 190.0)
        is_thermal_anomaly = data["temperature"] > 60.0
        assert is_voltage_anomaly or is_thermal_anomaly, "Sensor tampering must violate physical sensor bounds"


def test_network_degradation_characteristics(generator):
    for _ in range(50):
        data = generator.generate_network_degradation("device_001")
        assert data["is_anomaly"] == 1
        assert data["attack_type"] == "network_degradation"
        assert data["network_latency"] >= 200.0, "Network degradation must exhibit high latency"


def test_labeled_evaluation_dataset_structure(generator):
    df = generator.generate_labeled_evaluation_dataset(normal_samples=200, anomalies_per_type=25)

    # 200 normal + 4 * 25 anomalies = 300 total samples
    assert len(df) == 300
    assert df.isnull().sum().sum() == 0

    assert set(df["attack_type"].unique()) == {
        "normal",
        "dos_flooding",
        "brute_force_auth",
        "sensor_tampering",
        "network_degradation"
    }

    assert df["is_anomaly"].value_counts()[0] == 200
    assert df["is_anomaly"].value_counts()[1] == 100
