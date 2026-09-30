import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from storage.database import InfluxDBService

db = InfluxDBService()

q_table = """
from(bucket: "iot_telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "security_alerts")
  |> drop(columns: ["_start", "_stop", "_measurement"])
  |> pivot(rowKey:["_time", "device_id"], columnKey: ["_field"], valueColumn: "_value")
  |> group()
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: 5)
"""
tables = db.query_api.query(q_table)
print("=== Table Query Output ===")
for t in tables:
    for r in t.records:
        print("Record keys and values:")
        for k, v in r.values.items():
            print(f"  {k} -> {v}")
        break
    break

q_max_risk = """
from(bucket: "iot_telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "device_telemetry")
  |> filter(fn: (r) => r["_field"] == "calibrated_risk_score")
  |> group()
  |> max()
"""
tables2 = db.query_api.query(q_max_risk)
print("\n=== Max Risk Output ===")
for t in tables2:
    for r in t.records:
        print("Max Risk:", r.values.get("_value"))

q_count = """
from(bucket: "iot_telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "device_telemetry")
  |> filter(fn: (r) => r["_field"] == "temperature")
  |> group()
  |> count()
"""
tables3 = db.query_api.query(q_count)
print("\n=== Total Packets Output ===")
for t in tables3:
    for r in t.records:
        print("Total count:", r.values.get("_value"))
