
import requests
from bs4 import BeautifulSoup

url = "https://www.vakifkart.com.tr/kampanyalar/sayfa/1"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    items = soup.select("div.mainKampanyalarDesktop:not(.eczk) .list a.item")
    print(f"Status: {response.status_code}")
    print(f"Items found: {len(items)}")
    if items:
        print(f"First item: {items[0].get('href')}")
except Exception as e:
    print(f"Error: {e}")
