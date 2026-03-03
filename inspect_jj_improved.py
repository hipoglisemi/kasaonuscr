import requests
from bs4 import BeautifulSoup
import re

url = "https://dunyakatilim.com.tr/kampanyalar/jack-jones"
headers = {"User-Agent": "Mozilla/5.0"}
res = requests.get(url, headers=headers)
soup = BeautifulSoup(res.text, 'html.parser')

# Check multiple possible content containers
content_div = (
    soup.select_one('.blog-detail-content') or 
    soup.select_one('.richtext') or 
    soup.select_one('.content-area') or
    soup.select_one('.blog-detail-text') or
    soup.select_one('.s-content')
)

if content_div:
    raw_text = content_div.get_text(separator='\n', strip=True) 
else:
    raw_text = soup.body.get_text(separator='\n', strip=True) if soup.body else ""

print("RAW TEXT EXTRACTED:")
print("---")
print(raw_text)
print("---")
