import urllib.request
import urllib.parse
import json
import sys

def fetch_json(url, params=None):
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    print(f"Requesting: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "AERIS-WindAnalytics/1.0", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            return json.loads(data.decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        print(f"HTTPError {e.code}: {err_msg[:500]}")
        return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def main():
    # 1. Test FUELHH endpoint parameters
    print("--- 1. Testing FUELHH with query parameters ---")
    fuelhh_base = "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream"
    # Try settlementDate or publishTime or startTime
    for test_params in [
        {"settlementDateFrom": "2026-01-01", "settlementDateTo": "2026-01-01"},
        {"from": "2026-01-01T00:00:00Z", "to": "2026-01-01T02:00:00Z"},
        {"publishDateTimeFrom": "2026-01-01T00:00:00Z", "publishDateTimeTo": "2026-01-01T02:00:00Z"},
        {"startTime": "2026-01-01T00:00:00Z"},
        {"fuelType": "WIND"}
    ]:
        res = fetch_json(fuelhh_base, test_params)
        if res is not None:
            if isinstance(res, list):
                print(f"  Received list of {len(res)} items")
                if len(res) > 0:
                    print(f"  Sample item: {res[0]}")
            elif isinstance(res, dict):
                print(f"  Received dict with keys: {list(res.keys())}")
                if "data" in res:
                    print(f"  data length: {len(res['data'])}")
                    if len(res['data']) > 0:
                        print(f"  Sample item: {res['data'][0]}")

    print("\n--- 2. Testing WINDFOR with query parameters ---")
    windfor_base = "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream"
    for test_params in [
        {"publishDateTimeFrom": "2026-01-01T00:00:00Z", "publishDateTimeTo": "2026-01-01T02:00:00Z"},
        {"from": "2026-01-01T00:00:00Z", "to": "2026-01-01T02:00:00Z"},
        {"settlementDateFrom": "2026-01-01", "settlementDateTo": "2026-01-01"}
    ]:
        res = fetch_json(windfor_base, test_params)
        if res is not None:
            if isinstance(res, list):
                print(f"  Received list of {len(res)} items")
                if len(res) > 0:
                    print(f"  Sample item: {res[0]}")
            elif isinstance(res, dict):
                print(f"  Received dict with keys: {list(res.keys())}")

if __name__ == "__main__":
    main()
