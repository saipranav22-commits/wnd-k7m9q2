import urllib.request
import json

url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream?publishDateTimeFrom=2026-01-01T00:00:00Z&publishDateTimeTo=2026-01-01T04:00:00Z"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))

print(f"Total records in test window: {len(data)}")
by_pub = {}
for r in data:
    pub = r["publishTime"]
    by_pub.setdefault(pub, []).append(r)

for pub, records in sorted(by_pub.items()):
    print(f"\nPublishTime: {pub} (Records count: {len(records)})")
    starts = [r["startTime"] for r in records]
    print(f"  First 5 starts: {starts[:5]}")
    print(f"  Last 5 starts: {starts[-5:]}")
    # Check time delta between starts
    from datetime import datetime
    dt_starts = [datetime.fromisoformat(s.replace("Z", "+00:00")) for s in sorted(starts)]
    deltas = [(dt_starts[i+1] - dt_starts[i]).total_seconds() / 60 for i in range(len(dt_starts)-1)]
    print(f"  Deltas between consecutive starts (minutes): {set(deltas)}")
