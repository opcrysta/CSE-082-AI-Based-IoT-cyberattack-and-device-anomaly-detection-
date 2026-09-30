import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from storage.database import InfluxDBService

db = InfluxDBService()

q_current = """
from(bucket: "iot_telemetry")
  |> range(start: -2m)
  |> filter(fn: (r) => r["_measurement"] == "device_telemetry")
  |> filter(fn: (r) => r["_field"] == "calibrated_risk_score")
  |> filter(fn: (r) => r["device_id"] =~ /^device_00[1-3]$/)
  |> last()
  |> group()
  |> max()
"""

tables = db.query_api.query(q_current)
for t in tables:
    for r in t.records:
        print("Real-time Current Fleet Risk:", r.values.get("_value"))
