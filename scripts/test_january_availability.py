import urllib.request
import urllib.parse
import json

def test_january_availability():
    print("Testing FUELHH for 2026-01-01 to 2026-01-03...")
    fuelhh_url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream?settlementDateFrom=2026-01-01&settlementDateTo=2026-01-03&fuelType=WIND"
    req = urllib.request.Request(fuelhh_url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"FUELHH items returned: {len(data)}")
            if data:
                print(f"Sample: {data[0]}")
                print(f"Dates present: {sorted(list(set(d.get('settlementDate') for d in data)))}")
    except Exception as e:
        print(f"FUELHH error: {e}")

    print("\nTesting WINDFOR for 2026-01-01...")
    windfor_url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream?publishDateTimeFrom=2026-01-01T00:00:00Z&publishDateTimeTo=2026-01-02T00:00:00Z"
    req = urllib.request.Request(windfor_url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"WINDFOR items returned: {len(data)}")
            if data:
                print(f"Sample: {data[0]}")
                pub_times = sorted(list(set(d.get('publishTime') for d in data)))
                start_times = sorted(list(set(d.get('startTime') for d in data)))
                print(f"Publish times count: {len(pub_times)}, range: {pub_times[0]} to {pub_times[-1]}")
                print(f"Start times count: {len(start_times)}, range: {start_times[0]} to {start_times[-1]}")
    except Exception as e:
        print(f"WINDFOR error: {e}")

if __name__ == "__main__":
    test_january_availability()
