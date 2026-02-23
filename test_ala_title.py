import requests
from bs4 import BeautifulSoup

url = "https://www.turkiyefinansala.com/tr-tr/kampanyalar/Sayfalar/ala-aksa-2025.aspx"
headers = {"User-Agent": "Mozilla/5.0"}
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.content, "html.parser")

print(f"Title Tag: {soup.title.string.strip()}")
print(f"H1: {[h.get_text(strip=True) for h in soup.find_all('h1')]}")
print(f"H2: {[h.get_text(strip=True) for h in soup.find_all('h2')]}")
print(f"H3: {[h.get_text(strip=True) for h in soup.find_all('h3')]}")
print(f"H4: {[h.get_text(strip=True) for h in soup.find_all('h4')]}")

# Content search
content = soup.select_one(".ms-rtestate-field")
if content:
    print(f"Content Start: {content.get_text(strip=True)[:100]}")
    # Maybe first strong tag?
    strong = content.find("strong")
    if strong:
        print(f"First Strong: {strong.get_text(strip=True)}")
