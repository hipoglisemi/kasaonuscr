import requests
from bs4 import BeautifulSoup
import re
import json

url = "https://sipay.com.tr/kampanya/"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    print("\n--- Campaign Links ---")
    links = soup.find_all('a', href=re.compile(r'/kampanya/.*'))
    unique_links = set()
    
    for link in links:
        href = link.get('href', '')
        if href == '/kampanya/' or href == 'https://sipay.com.tr/kampanya/':
            continue
            
        if href not in unique_links:
            unique_links.add(href)
            
            # Find closest parent container to extract title and image
            parent = link.find_parent('div')
            
            # Find image
            img = link.find('img')
            if not img and parent:
                img = parent.find('img')
                
            img_url = "N/A"
            if img:
                img_url = img.get('src') or img.get('data-src', 'N/A')
                
            # Find title
            title_el = link.find(['h2', 'h3', 'h4'])
            if not title_el and parent:
                title_el = parent.find(['h2', 'h3', 'h4'])
            
            title = title_el.text.strip() if title_el else link.text.strip()
            # if title is empty, maybe try to check nearby siblings
            if not title and parent:
                sibling_text = parent.text.strip()
                title = sibling_text[:50] + "..." if len(sibling_text) > 50 else sibling_text
                
            print(f"[{len(unique_links)}] URL: {href}")
            print(f"    Title: {title}")
            print(f"    Img:   {img_url}")
            print("-" * 50)
            
            if len(unique_links) >= 5:
                break
                
    # Next.js structure inspection
    next_data = soup.find('script', id='__NEXT_DATA__')
    if next_data:
        try:
            data = json.loads(next_data.string)
            print("\n--- Found __NEXT_DATA__ ---")
            
            # Navigate nested structure
            if 'props' in data and 'pageProps' in data['props']:
                page_props = data['props']['pageProps']
                print(f"Keys in pageProps: {list(page_props.keys())}")
                
                # Try to find campaigns array
                for key, val in page_props.items():
                    if isinstance(val, list):
                        print(f"Array '{key}' has {len(val)} items")
                        if len(val) > 0 and isinstance(val[0], dict):
                            print(f"  First item keys: {list(val[0].keys())}")
                            # Print a snippet of the first item
                            import pprint
                            pprint.pprint(val[0], depth=2)
                    elif isinstance(val, dict):
                        print(f"Dict '{key}' keys: {list(val.keys())}")
                        
        except Exception as e:
            print(f"Failed to parse NEXT_DATA: {e}")
            
except Exception as e:
    print(f"Error: {e}")
