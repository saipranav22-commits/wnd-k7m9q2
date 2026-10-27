import urllib.request
import re

def scrape_doc(url):
    print(f"Scraping doc: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8")
            # find text or json
            print(f"Length of html: {len(html)}")
            # look for parameter names
            params = re.findall(r'name="([^"]+)"|class="parameter[^"]*">([^<]+)<|`([a-zA-Z0-9_]+)`', html)
            print("Found potential parameters / tokens:", set([p for group in params for p in group if p])[:20])
    except Exception as e:
        print(f"Failed to scrape {url}: {e}")

scrape_doc("https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream")
scrape_doc("https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream")
