
import requests
import json

def debug_api():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    })
    
    print("--- 1. Simple GET (CURL-like) ---")
    r1 = session.get("https://www.wingscard.com.tr/api/campaign/list?page=1")
    print(f"Status: {r1.status_code}")
    try:
        data = r1.json()
        print(f"Found: {len(data.get('campaigns', []))} campaigns")
        if len(data.get('campaigns', [])) == 0:
            print(f"Full JSON: {json.dumps(data, indent=2)[:500]}...")
    except:
        print("Not JSON")

    print("\n--- 2. GET after visiting homepage (Session Init) ---")
    session.get("https://www.wingscard.com.tr/")
    r2 = session.get("https://www.wingscard.com.tr/api/campaign/list?page=1")
    print(f"Status: {r2.status_code}")
    try:
        data = r2.json()
        print(f"Found: {len(data.get('campaigns', []))} campaigns")
    except:
        print("Not JSON")

    print("\n--- 3. GET with specific Accept header ---")
    session.headers['Accept'] = 'application/json, text/plain, */*'
    r3 = session.get("https://www.wingscard.com.tr/api/campaign/list?page=1")
    print(f"Status: {r3.status_code}")
    try:
        data = r3.json()
        print(f"Found: {len(data.get('campaigns', []))} campaigns")
    except:
        print("Not JSON")

if __name__ == "__main__":
    debug_api()
