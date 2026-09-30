"""
Automated Pytest for Milestone 9: Grafana Visualizations & Provisioning.
Tests dashboard JSON validity, panel schema integrity, and live Grafana API provisioning.
"""

import json
import urllib.request
import base64
import pytest
from pathlib import Path
from config.settings import BASE_DIR


def test_grafana_dashboard_json_integrity():
    dashboard_file = BASE_DIR / "grafana" / "iot_security_dashboard.json"
    assert dashboard_file.exists(), "Dashboard JSON must exist in grafana/ directory"

    with open(dashboard_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["title"] == "IoT Cyberattack & Anomaly Detection Dashboard"
    assert data["uid"] == "iot-security-overview"

    # Verify key panels exist
    panel_titles = [p.get("title") for p in data["panels"] if "title" in p]
    assert "Current Anomaly Risk Level" in panel_titles
    assert "Physical Sensors: Temperature & Voltage" in panel_titles
    assert "Network & Compute Saturation (DoS Floods)" in panel_titles
    assert "Recent Security Incident Feed" in panel_titles


def test_grafana_api_and_provisioning():
    # Verify Grafana HTTP API is responding
    try:
        req = urllib.request.Request("http://localhost:3000/api/health")
        with urllib.request.urlopen(req, timeout=3) as resp:
            health = json.loads(resp.read())
            assert health.get("database") == "ok"
    except Exception as e:
        pytest.skip(f"Grafana container not reachable over localhost:3000 ({e})")

    # Check Provisioned Datasources
    auth = base64.b64encode(b"admin:admin").decode()
    headers = {"Authorization": f"Basic {auth}"}

    req_ds = urllib.request.Request("http://localhost:3000/api/datasources", headers=headers)
    with urllib.request.urlopen(req_ds, timeout=3) as resp:
        datasources = json.loads(resp.read())
        ds_names = [d["name"] for d in datasources]
        assert "InfluxDB_IoT" in ds_names, "InfluxDB_IoT datasource must be automatically provisioned"

    # Check Provisioned Dashboard
    req_dash = urllib.request.Request("http://localhost:3000/api/search", headers=headers)
    with urllib.request.urlopen(req_dash, timeout=3) as resp:
        dashboards = json.loads(resp.read())
        titles = [d.get("title") for d in dashboards]
        assert any("IoT Cyberattack" in t for t in titles), "Dashboard must be provisioned in Grafana"
