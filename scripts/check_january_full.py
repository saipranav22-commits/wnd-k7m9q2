import urllib.request
import json
from datetime import datetime, timedelta

def check_january_full():
    print("Checking FUELHH for all January 2026...")
    url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream?settlementDateFrom=2026-01-01&settlementDateTo=2026-02-02&fuelType=WIND"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            actuals = json.loads(resp.read().decode("utf-8"))
            print(f"FUELHH records for 2026-01-01 to 2026-02-02: {len(actuals)}")
            dates = sorted(list(set(r.get("settlementDate") for r in actuals)))
            print(f"Dates covered in FUELHH ({len(dates)} days): {dates[0]} to {dates[-1]}")
    except Exception as e:
        print(f"FUELHH error: {e}")

    print("\nChecking WINDFOR for January 2026...")
    # Let's test a chunk of 5 days
    url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream?publishDateTimeFrom=2026-01-01T00:00:00Z&publishDateTimeTo=2026-01-05T00:00:00Z"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            forecasts = json.loads(resp.read().decode("utf-8"))
            print(f"WINDFOR records for Jan 1-5: {len(forecasts)}")
            pubs = sorted(list(set(r.get("publishTime") for r in forecasts)))
            print(f"Distinct publication times ({len(pubs)}): {pubs[0]} to {pubs[-1]}")
    except Exception as e:
        print(f"WINDFOR error: {e}")

if __name__ == "__main__":
    check_january_full()
