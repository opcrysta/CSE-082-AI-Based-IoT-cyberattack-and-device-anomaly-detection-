import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from storage.database import InfluxDBService

db = InfluxDBService()

# Test condition logic
device_var = "All"
q = f"""
from(bucket: "iot_telemetry")
  |> range(start: -15m)
  |> filter(fn: (r) => r["_measurement"] == "device_telemetry")
  |> filter(fn: (r) => r["_field"] == "temperature")
  |> filter(fn: (r) => if "{device_var}" == "All" then r["device_id"] =~ /^device_00[1-3]$/ else r["device_id"] == "{device_var}")
  |> aggregateWindow(every: 10s, fn: mean, createEmpty: false)
  |> limit(n: 5)
"""

tables = db.query_api.query(q)
print("Query executed successfully! Records:")
for t in tables:
    for r in t.records:
        print(f"  {r.values.get('device_id')} -> {r.values.get('_value'):.2f}")
