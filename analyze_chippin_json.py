import json
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def analyze_json():
    try:
        with open("chippin_raw.html", "r", encoding="utf-8") as f:
            html = f.read()
            
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", {"id": "__NEXT_DATA__"})
        
        if script:
            data = json.loads(script.string)
            print("✅ JSON Parsed Successfully")
            
            # Navigate to props
            props = data.get("props", {})
            page_props = props.get("pageProps", {})
            
            print("Keys in pageProps:", page_props.keys())
            
            # Look for campaigns
            if "campaigns" in page_props:
                campaigns = page_props["campaigns"]
                print(f"Found {len(campaigns)} campaigns directly in pageProps.")
                if len(campaigns) > 0:
                    c = campaigns[0]
                    print(f"\n--- Sample Campaign Keys ({len(c)} keys) ---")
                    print(sorted(c.keys()))
                    
                    print("\n--- URL Analysis ---")
                    print("webName:", c.get("webName"))
                    print("id:", c.get("id"))
                    
                    # Look for URL related fields
                    url_fields = [k for k in c.keys() if "url" in k.lower() or "seo" in k.lower() or "slug" in k.lower() or "link" in k.lower()]
                    print("Potential URL Fields:", url_fields)
                    for f in url_fields:
                        print(f"{f}: {c.get(f)}")

            # Analyze Root Keys for Config
            print("\n--- Root Keys ---")
            print(data.keys())
            if "runtimeConfig" in data:
                print("Runtime Config:", data["runtimeConfig"])
            else:
                # Dig deeper
                for k, v in page_props.items():
                    if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                        print(f"Potential list found in key '{k}' with length {len(v)}")
                        print("Sample keys:", v[0].keys())

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_json()
