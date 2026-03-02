import requests
import re
from bs4 import BeautifulSoup
import json

url = "https://sipay.com.tr/kampanya/"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print(f"Fetching {url}...")
try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        html = response.text
        with open('sipay_kampanya.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Saved HTML to sipay_kampanya.html")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for API endpoints in Javascript
        scripts = soup.find_all('script')
        print(f"\nAnalyzing {len(scripts)} script tags...")
        
        next_data = soup.find('script', id='__NEXT_DATA__')
        if next_data:
            print("FOUND Next.js __NEXT_DATA__!")
            data = json.loads(next_data.string)
            print(f"Keys in NEXT_DATA: {list(data.keys())}")
            if 'props' in data:
                print(f"Keys in props: {list(data['props'].keys())}")
                if 'pageProps' in data['props']:
                    print(f"Keys in pageProps: {list(data['props']['pageProps'].keys())}")
                    
        nuxt_data = soup.find('script', string=re.compile(r'__NUXT__'))
        if nuxt_data:
            print("FOUND Nuxt.js data!")
            
        if 'wp-json' in html:
            print("FOUND wp-json (WordPress REST API) references!")
            
        print("\nLooking for list items...")
        # Just print some text to see what kind of campaigns are there
        links = soup.find_all('a', href=re.compile(r'/kampanya/.*'))
        print(f"Found {len(links)} links containing '/kampanya/'")
        for i, link in enumerate(links[:5]):
            print(f"  {link.get('href')} - {link.text.strip()[:50]}")
            
except Exception as e:
    print(f"Error: {e}")
