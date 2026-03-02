import requests
from bs4 import BeautifulSoup

url = "https://param.com.tr/tum-avantajlar"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, 'html.parser')

links = set()
for a in soup.select('a[href^="/avantajlar/"]'):
    href = a.get('href')
    if href and href != '/avantajlar/':
        links.add(href)

print(f"Status: {resp.status_code}")
print(f"Total campaign links found via simple GET: {len(links)}")
if links:
    print(f"Example link: {list(links)[0]}")
