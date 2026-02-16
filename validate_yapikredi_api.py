
import requests
import json
from datetime import datetime

# Config from play.ts
BASE_URL = 'https://www.yapikrediplay.com.tr'
LIST_API_URL = 'https://www.yapikrediplay.com.tr/api/campaigns?campaignSectorId=dfe87afe-9b57-4dfd-869b-c87dd00b85a1&campaignSectorKey=tum-kampanyalar'

def validate_api():
    print(f"Testing API: {LIST_API_URL}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f'{BASE_URL}/kampanyalar',
        'Accept': 'application/json, text/plain, */*',
        'page': '1'
    }

    try:
        response = requests.get(LIST_API_URL, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('Items', [])
            print(f"Found {len(items)} items in response.")
            
            if items:
                first = items[0]
                print(f"Sample Item: {first.get('Title')}")
                print(f"Url: {first.get('Url')}")
                print(f"ImageUrl: {first.get('ImageUrl')}")
                print(f"EndDate: {first.get('EndDate')}")
                return True
            else:
                print("Response is valid but empty items list.")
        else:
            print(f"Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")
        
    return False

if __name__ == "__main__":
    validate_api()
