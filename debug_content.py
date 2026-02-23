import requests
from bs4 import BeautifulSoup

urls = [
    "https://www.turkiyefinansala.com/tr-tr/kampanyalar/Sayfalar/ala-aksa-2025.aspx",
    "https://www.happycard.com.tr/kampanyalar/Sayfalar/Erkenrezervasyon.aspx"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

for url in urls:
    print(f"\n--- Checking: {url} ---")
    try:
        r = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(r.content, "html.parser")
        
        # Check title
        print(f"Title: {soup.title.string.strip() if soup.title else 'No Title'}")
        
        # Check specific content selectors used in scraper
        s1 = soup.select_one(".ms-rtestate-field")
        s2 = soup.select_one(".campaign-description")
        
        print(f"Selector .ms-rtestate-field found: {bool(s1)}")
        if s1: print(f"Preview s1: {s1.get_text(strip=True)[:100]}")
        
        s2_len = len(soup.select(".campaign-detail"))
        print(f"Class .campaign-detail count: {s2_len}")
        
        # Print body text preview to see if main content exists
        body_text = soup.body.get_text(separator=" ", strip=True)
        print(f"Body text preview: {body_text[:200]}")
        
        # Look for specific keywords in raw HTML
        if "kampanya koşulları" in r.text.lower():
            print("Keyword 'kampanya koşulları' FOUND in raw HTML.")
        else:
            print("Keyword 'kampanya koşulları' NOT FOUND in raw HTML.")
            
    except Exception as e:
        print(f"Error: {e}")
