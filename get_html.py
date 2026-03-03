import requests
from bs4 import BeautifulSoup

url = "https://dunyakatilim.com.tr/kampanyalar/jack-jones"
headers = {"User-Agent": "Mozilla/5.0"}
res = requests.get(url, headers=headers)
soup = BeautifulSoup(res.text, 'html.parser')

print(soup.prettify()[:2000])
print("\n---FINDING CONTENT DIVS---\n")
for div in soup.find_all('div', style=True):
    if "text" in div.get_text().lower() or "kampanya" in div.get_text().lower():
        print(f"Div classes: {div.get('class')}")
        
for section in soup.select('section, .content, .detail, .kampanya'):
    print(f"Section classes: {section.get('class')}")
