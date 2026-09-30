import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from storage.database import InfluxDBService

db = InfluxDBService()

q = """
from(bucket: "iot_telemetry")
  |> range(start: -5m)
  |> filter(fn: (r) => r["_measurement"] == "device_telemetry")
  |> filter(fn: (r) => r["_field"] == "calibrated_risk_score")
  |> group(columns: ["device_id"])
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: 1)
"""

tables = db.query_api.query(q)
for t in tables:
    for r in t.records:
        print(r.values.get("_time"), r.values.get("device_id"), "Latest Risk:", r.values.get("_value"))
