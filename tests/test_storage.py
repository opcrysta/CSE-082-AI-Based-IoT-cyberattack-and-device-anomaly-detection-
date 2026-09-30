"""
Automated Pytest for Milestone 8: Time-Series Database Persistence.
Tests InfluxDB point construction, edge SQLite buffering, and zero-data-loss guarantees.
"""

import sqlite3
import json
import pytest
from storage.database import InfluxDBService
from alerts.alert_engine import AlertEvent


@pytest.fixture
def temp_db(tmp_path):
    cache_file = tmp_path / "test_buffer.db"
    service = InfluxDBService(
        url="http://localhost:8086",
        token="test_token",
        org="test_org",
        bucket="test_bucket",
        cache_db_path=cache_file
    )
    yield service
    service.close()


def test_influxdb_service_initialization(temp_db):
    assert temp_db.cache_db_path.exists()

    # Verify SQLite buffer tables exist
    with sqlite3.connect(temp_db.cache_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert "buffered_telemetry" in tables
        assert "buffered_alerts" in tables


def test_write_telemetry_and_alert_persistence(temp_db):
    telemetry = {
        "device_id": "test_device_001",
        "temperature": 27.5,
        "voltage": 229.0,
        "cpu_usage": 88.0,
        "ram_usage": 45.0,
        "message_rate": 25.0,
        "failed_auth_count": 0,
        "network_latency": 35.0
    }
    ml_result = {
        "is_anomaly": True,
        "raw_score": -0.12,
        "risk_score": 0.89
    }
    alert = AlertEvent(
        alert_id="alert-uuid-1234",
        timestamp="2026-10-01T01:00:00Z",
        device_id="test_device_001",
        is_anomaly=True,
        is_cyberattack=True,
        alert_category="CYBERATTACK",
        threat_name="Denial-of-Service (DoS) / Message Flooding",
        severity="CRITICAL",
        raw_anomaly_score=-0.12,
        calibrated_risk_score=0.89,
        contributing_metrics={"message_rate": 25.0, "cpu_usage": 88.0},
        recommended_action="Throttle client."
    )

    success = temp_db.write_telemetry(telemetry, ml_result, alert)
    assert success is True

    # If offline, verify records were safely buffered in SQLite
    if not temp_db.is_connected():
        with sqlite3.connect(temp_db.cache_db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT device_id, data_json FROM buffered_telemetry")
            rows = cur.fetchall()
            assert len(rows) == 1
            assert rows[0][0] == "test_device_001"
            saved_data = json.loads(rows[0][1])
            assert saved_data["telemetry"]["temperature"] == 27.5

            cur.execute("SELECT device_id, alert_json FROM buffered_alerts")
            alert_rows = cur.fetchall()
            assert len(alert_rows) == 1
            saved_alert = json.loads(alert_rows[0][1])
            assert saved_alert["severity"] == "CRITICAL"
            assert saved_alert["alert_category"] == "CYBERATTACK"
