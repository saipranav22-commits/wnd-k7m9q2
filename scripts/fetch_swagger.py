import urllib.request
import json

url = "https://data.elexon.co.uk/swagger/v1/swagger.json"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print("Successfully downloaded swagger.json!")
        with open("elexon_swagger.json", "w") as f:
            json.dump(data, f, indent=2)
        paths = data.get("paths", {})
        for p, methods in paths.items():
            if "datasets" in p or "fuelhh" in p.lower() or "windfor" in p.lower():
                print(f"\nPath: {p}")
                for m, info in methods.items():
                    print(f"  Method: {m.upper()} - {info.get('summary')}")
                    for param in info.get("parameters", []):
                        print(f"    Param: {param.get('name')} ({param.get('in')}, required={param.get('required')}) - {param.get('description')}")
except Exception as e:
    print(f"Error: {e}")
