import urllib.request
import re

url = 'https://bmrs.elexon.co.uk/static/js/main.63973561.js'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as r:
        js = r.read().decode('utf-8', errors='ignore')
        matches = re.findall(r'https?://[^\s"\'\\]+|/[a-zA-Z0-9_\-\./]+\.json', js)
        for m in sorted(set(matches)):
            print(m)
except Exception as e:
    print(f"Error: {e}")
