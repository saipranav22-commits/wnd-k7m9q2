import urllib.request
import json

url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream?publishDateTimeFrom=2026-01-01T00:00:00Z&publishDateTimeTo=2026-01-02T00:00:00Z"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))

start_minutes = set()
for r in data:
    # check minutes of startTime
    time_part = r["startTime"].split("T")[1]
    start_minutes.add(time_part)

print(f"Unique start time strings (time of day): {sorted(list(start_minutes))}")
