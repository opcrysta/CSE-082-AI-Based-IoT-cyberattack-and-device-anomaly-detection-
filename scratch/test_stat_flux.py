import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from storage.database import InfluxDBService

db = InfluxDBService()

q = """
from(bucket: "iot_telemetry")
  |> range(start: -15m)
  |> filter(fn: (r) => r["_measurement"] == "device_telemetry")
  |> filter(fn: (r) => r["_field"] == "is_anomaly")
  |> filter(fn: (r) => r["device_id"] =~ /^device_00[1-3]$/)
  |> aggregateWindow(every: 1m, fn: sum, createEmpty: false)
"""

tables = db.query_api.query(q)
print("Aggregate window anomaly records:")
for t in tables:
    for r in t.records:
        print(f"  {r.values.get('_time')} -> {r.values.get('_value')}")
