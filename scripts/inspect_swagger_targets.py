import json

with open("elexon_swagger.json", "r") as f:
    spec = json.load(f)

for path, info in spec.get("paths", {}).items():
    if "FUELHH" in path or "WINDFOR" in path:
        print(f"\n==============================")
        print(f"PATH: {path}")
        for method, details in info.items():
            print(f"METHOD: {method.upper()}")
            print(f"SUMMARY: {details.get('summary')}")
            print(f"DESCRIPTION: {details.get('description')}")
            print("PARAMETERS:")
            for p in details.get("parameters", []):
                print(f"  - {p.get('name')} in {p.get('in')} (req={p.get('required')}, type={p.get('schema', {}).get('type')}, format={p.get('schema', {}).get('format')}): {p.get('description')}")
            print("RESPONSES:")
            for code, resp in details.get("responses", {}).items():
                print(f"  {code}: {resp.get('description')}")
