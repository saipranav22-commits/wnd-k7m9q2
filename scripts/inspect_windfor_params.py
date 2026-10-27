import urllib.request
import json

def main():
    # Try to get openapi spec or swagger
    urls = [
        "https://data.elexon.co.uk/bmrs/api/v1/openapi.json",
        "https://data.elexon.co.uk/bmrs/api/v1/swagger/v1/swagger.json",
        "https://data.elexon.co.uk/bmrs/api/v1/api-docs",
        "https://bmrs.elexon.co.uk/api-documentation/openapi.json"
    ]
    for u in urls:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                print(f"Found spec at {u}!")
                # Search for datasets/WINDFOR
                paths = data.get("paths", {})
                for path, methods in paths.items():
                    if "WINDFOR" in path or "FUELHH" in path:
                        print(f"Path: {path}")
                        for m, details in methods.items():
                            print(f"  Method: {m}, summary: {details.get('summary')}")
                            for param in details.get("parameters", []):
                                print(f"    param: {param.get('name')} in {param.get('in')} ({param.get('schema', {}).get('type')}) - {param.get('description')}")
                return
        except Exception as e:
            print(f"Not found {u}: {e}")

    # If openapi json not directly at those URLs, let's test specific WINDFOR parameters:
    print("Testing candidate WINDFOR parameters...")
    base = "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream"
    # What are common Elexon parameters?
    candidates = [
        {"publishDateTimeFrom": "2026-01-01T00:00:00Z", "publishDateTimeTo": "2026-01-02T00:00:00Z"},
        {"settlementDateFrom": "2026-01-01", "settlementDateTo": "2026-01-02"},
        {"startTimeFrom": "2026-01-01T00:00:00Z", "startTimeTo": "2026-01-02T00:00:00Z"},
        {"from": "2026-01-01T00:00:00Z", "to": "2026-01-02T00:00:00Z"},
        {"publishTimeFrom": "2026-01-01T00:00:00Z", "publishTimeTo": "2026-01-02T00:00:00Z"},
    ]
    for c in candidates:
        url = f"{base}?{urllib.parse.urlencode(c)}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                items = json.loads(resp.read().decode("utf-8"))
                print(f"Query {c}: {len(items)} items")
                if items:
                    print(f"   First: pub={items[0].get('publishTime')} start={items[0].get('startTime')}")
                    print(f"   Last:  pub={items[-1].get('publishTime')} start={items[-1].get('startTime')}")
        except Exception as err:
            print(f"Query {c} failed: {err}")

if __name__ == "__main__":
    import urllib.parse
    main()
