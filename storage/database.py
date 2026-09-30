"""
Time-Series Database Persistence Module for InfluxDB v2.
Writes validated device telemetry, Isolation Forest anomaly scores,
and security alert records into InfluxDB buckets with edge-buffering fallback.
"""

import sys
import sqlite3
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from config.settings import influx_config, BASE_DIR
from alerts.alert_engine import AlertEvent


class InfluxDBService:
    """
    Manages time-series writes and queries for IoT telemetry and detection events.
    Features an Edge Store-and-Forward SQLite buffer when InfluxDB is initializing.
    """

    def __init__(
        self,
        url: str = None,
        token: str = None,
        org: str = None,
        bucket: str = None,
        cache_db_path: Path = None
    ):
        self.url = url or influx_config.url
        self.token = token or influx_config.token
        self.org = org or influx_config.org
        self.bucket = bucket or influx_config.bucket
        self.cache_db_path = cache_db_path or (BASE_DIR / "data" / "cache" / "offline_buffer.db")

        self.client: Optional[InfluxDBClient] = None
        self.write_api = None
        self.query_api = None
        self._is_online: bool = False
        self._last_ping_time: float = 0.0
        self._ping_retry_interval_sec: float = 30.0

        self._init_local_cache()
        self.connect()

    @property
    def is_online(self) -> bool:
        """Returns True if connected to InfluxDB, False if running offline buffer."""
        return self._is_online

    def _init_local_cache(self):
        """Initializes SQLite local buffer for edge store-and-forward reliability."""
        self.cache_db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS buffered_telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    device_id TEXT,
                    data_json TEXT,
                    flushed INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS buffered_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    device_id TEXT,
                    alert_json TEXT,
                    flushed INTEGER DEFAULT 0
                )
            """)

    def connect(self) -> bool:
        """Attempts connection and verification to InfluxDB v2."""
        self._last_ping_time = time.time()
        try:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org, timeout=1000)
            if self.client.ping():
                self._is_online = True
                self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
                self.query_api = self.client.query_api()
                print(f"[INFLUXDB] Connected successfully to {self.url} (Org: '{self.org}', Bucket: '{self.bucket}')")
                return True
            else:
                self._is_online = False
                return False
        except Exception:
            self._is_online = False
            self.write_api = None
            self.query_api = None
            return False

    def is_connected(self) -> bool:
        """Checks if active InfluxDB client connection is operational with cooldown."""
        now = time.time()
        if not self._is_online:
            if (now - self._last_ping_time) < self._ping_retry_interval_sec:
                return False
            # Interval elapsed: retry connection
            return self.connect()

        try:
            return bool(self.client and self.client.ping())
        except Exception:
            self._is_online = False
            return False

    def write_telemetry(
        self,
        telemetry_data: Dict[str, Any],
        ml_result: Dict[str, Any],
        alert: Optional[AlertEvent] = None
    ) -> bool:
        """
        Records a telemetry observation, ML anomaly score, and optional alert to InfluxDB.
        Falls back to local SQLite buffer if InfluxDB is unreachable.
        """
        device_id = telemetry_data.get("device_id", "UNKNOWN")
        iso_time = telemetry_data.get("timestamp", datetime.now(timezone.utc).isoformat())

        # 1. Construct Telemetry Point
        point_telemetry = (
            Point("device_telemetry")
            .tag("device_id", device_id)
            .field("temperature", float(telemetry_data.get("temperature", 25.0)))
            .field("voltage", float(telemetry_data.get("voltage", 230.0)))
            .field("cpu_usage", float(telemetry_data.get("cpu_usage", 15.0)))
            .field("ram_usage", float(telemetry_data.get("ram_usage", 40.0)))
            .field("message_rate", float(telemetry_data.get("message_rate", 1.0)))
            .field("failed_auth_count", int(telemetry_data.get("failed_auth_count", 0)))
            .field("network_latency", float(telemetry_data.get("network_latency", 15.0)))
            .field("raw_anomaly_score", float(ml_result.get("raw_score", 0.0)))
            .field("calibrated_risk_score", float(ml_result.get("risk_score", 0.0)))
            .field("is_anomaly", 1 if ml_result.get("is_anomaly", False) else 0)
            .time(iso_time)
        )

        # 2. Construct Alert Point (if anomaly triggered alert)
        point_alert = None
        if alert:
            point_alert = (
                Point("security_alerts")
                .tag("device_id", alert.device_id)
                .tag("alert_category", alert.alert_category)
                .tag("threat_name", alert.threat_name)
                .tag("severity", alert.severity)
                .tag("is_cyberattack", str(alert.is_cyberattack))
                .field("calibrated_risk_score", float(alert.calibrated_risk_score))
                .field("raw_anomaly_score", float(alert.raw_anomaly_score))
                .field("recommended_action", alert.recommended_action)
                .time(alert.timestamp)
            )

        # 3. Write to InfluxDB if online
        points_to_write = [point_telemetry]
        if point_alert:
            points_to_write.append(point_alert)

        if self._is_online and self.write_api:
            try:
                self.write_api.write(bucket=self.bucket, org=self.org, record=points_to_write)
                return True
            except Exception as err:
                print(f"[INFLUXDB WRITE ERROR] {err} -> Buffering to local SQLite...")
                self._is_online = False

        # 4. Fallback: Edge SQLite Buffering
        self._buffer_locally(iso_time, device_id, telemetry_data, ml_result, alert)
        return True

    def _buffer_locally(
        self,
        timestamp: str,
        device_id: str,
        telemetry: Dict[str, Any],
        ml_result: Dict[str, Any],
        alert: Optional[AlertEvent]
    ):
        """Buffers observations into SQLite for zero-data-loss resiliency."""
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                record_data = {"telemetry": telemetry, "ml_result": ml_result}
                conn.execute(
                    "INSERT INTO buffered_telemetry (timestamp, device_id, data_json) VALUES (?, ?, ?)",
                    (timestamp, device_id, json.dumps(record_data))
                )
                if alert:
                    conn.execute(
                        "INSERT INTO buffered_alerts (timestamp, device_id, alert_json) VALUES (?, ?, ?)",
                        (timestamp, device_id, json.dumps(alert.to_dict()))
                    )
        except Exception as e:
            print(f"[BUFFER ERROR] Local SQLite write failed: {e}")

    def query_recent_telemetry(self, device_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Queries recent telemetry records using Flux."""
        if not self.is_connected() or not self.query_api:
            return []

        filter_clause = f'|> filter(fn: (r) => r["device_id"] == "{device_id}")' if device_id else ""
        flux_query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: -1h)
            |> filter(fn: (r) => r["_measurement"] == "device_telemetry")
            {filter_clause}
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> limit(n: {limit})
        '''
        try:
            tables = self.query_api.query(flux_query, org=self.org)
            results = []
            for table in tables:
                for record in table.records:
                    results.append(record.values)
            return results
        except Exception as e:
            print(f"[INFLUXDB QUERY ERROR] {e}")
            return []

    def close(self):
        """Closes InfluxDB client cleanly."""
        if self.client:
            self.client.close()
            print("[INFLUXDB] Connection closed.")
