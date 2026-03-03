import requests
from bs4 import BeautifulSoup
import re

url = "https://dunyakatilim.com.tr/kampanyalar/jack-jones"
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html, */*; q=0.01"
}

res = requests.get(url, headers=headers)
soup = BeautifulSoup(res.text, 'html.parser')

content_div = soup.select_one('.bt') or soup.select_one('.richtext') or soup.find('h2', text=re.compile('Kampanya Koşulları', re.I))

if content_div and content_div.parent:
    raw_text = content_div.parent.get_text(separator='\n', strip=True) 
else:
    raw_text = soup.body.get_text(separator='\n', strip=True) if soup.body else ""

print("RAW TEXT EXTRACTED:")
print("---")
print(raw_text)
print("---")
