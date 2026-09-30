"""
Automated Pytest for Milestone 3: Multi-Device Telemetry Simulator.
Tests device telemetry generation, statistical bounds, and dataset export.
"""

import pytest
import pandas as pd
from config.settings import model_config
from simulator.device_simulator import IoTDevice, MultiDeviceSimulator


def test_iot_device_normal_telemetry_schema():
    device = IoTDevice("device_001", random_state=42)
    telemetry = device.generate_normal_telemetry()

    assert telemetry["device_id"] == "device_001"
    assert "timestamp" in telemetry

    # Verify all ML feature columns are present in telemetry
    for col in model_config.feature_columns:
        assert col in telemetry, f"Missing feature column: {col}"


def test_iot_device_normal_telemetry_bounds():
    device = IoTDevice("device_002", random_state=123)

    # Sample 100 observations to test distribution bounds
    for _ in range(100):
        t = device.generate_normal_telemetry()

        assert 15.0 <= t["temperature"] <= 40.0
        assert 215.0 <= t["voltage"] <= 245.0
        assert 2.0 <= t["cpu_usage"] <= 40.0
        assert 20.0 <= t["ram_usage"] <= 65.0
        assert 0.5 <= t["message_rate"] <= 1.5
        assert t["failed_auth_count"] in (0, 1)  # Normal conditions: 0 or rare transient 1
        assert 5.0 <= t["network_latency"] <= 40.0


def test_multi_device_simulator_batch_generation(tmp_path):
    num_devices = 3
    samples_per_device = 50
    simulator = MultiDeviceSimulator(num_devices=num_devices, random_state=42)

    df = simulator.generate_batch_dataset(samples_per_device=samples_per_device)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == num_devices * samples_per_device
    assert df.isnull().sum().sum() == 0  # Zero missing values

    # Test saving to CSV
    csv_file = tmp_path / "test_baseline.csv"
    simulator.save_baseline_csv(csv_file, samples_per_device=samples_per_device)
    assert csv_file.exists()

    loaded_df = pd.read_csv(csv_file)
    assert len(loaded_df) == len(df)
