import urllib.request
import json
import base64

auth = base64.b64encode(b"admin:admin").decode()
req = urllib.request.Request(
    "http://localhost:3000/api/dashboards/uid/iot-security-overview",
    headers={"Authorization": f"Basic {auth}"}
)

with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read())
    d = res["dashboard"]
    print("Dashboard Title:", d["title"])
    print("Version:", d.get("version"))
    print("Panels Loaded:")
    for p in d.get("panels", []):
        if "title" in p:
            print(f"  - [{p.get('type')}] {p['title']}")
