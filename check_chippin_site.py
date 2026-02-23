import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

urls_to_check = [
    "https://www.chippin.com",
    "https://www.chippin.com.tr",
    "https://chippin.com.tr",
    "https://www.chippin.com/kampanyalar",
    "https://www.chippin.com.tr/kampanyalar"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

for url in urls_to_check:
    print(f"\nChecking {url}...")
    try:
        r = requests.get(url, headers=headers, timeout=10, verify=False)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, "html.parser")
            title = soup.title.string.strip() if soup.title else 'No Title'
            print(f"Title: {title}")
            
            # Check for campaign links if checking campaign page
            if "kampanya" in url:
                links = soup.find_all("a")
                # Look for hrefs containing 'kampanya' or 'detay'
                c_links = [a.get('href') for a in links if a.get('href') and ('kampanya' in a.get('href') or 'detay' in a.get('href'))]
                print(f"Found {len(c_links)} potential campaign links.")
                if c_links:
                    print(f"Sample: {c_links[0]}")
                
                # Check for Next.js data
                if "__NEXT_DATA__" in r.text:
                    print("✅ FOUND __NEXT_DATA__ JSON blob!")
                    with open("chippin_raw.html", "w", encoding="utf-8") as f:
                        f.write(r.text)
                    print("Saved HTML to chippin_raw.html")
                else:
                    print("❌ __NEXT_DATA__ not found.")

    except Exception as e:
        print(f"Error: {e}")
