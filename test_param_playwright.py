from playwright.sync_api import sync_playwright
import time
from bs4 import BeautifulSoup
import re

url = "https://param.com.tr/tum-avantajlar"

def test_param():
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        print(f"Navigating to {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(3) # Wait for initial hydration
        
        soup = BeautifulSoup(page.content(), 'html.parser')
        initial_links = set([a['href'] for a in soup.select('a[href^="/avantajlar/"]') if a['href'] != '/avantajlar/'])
        print(f"Initial unique campaign links found: {len(initial_links)}")
        
        print("Scrolling down to lazy load items as requested by user...")
        last_height = page.evaluate("document.body.scrollHeight")
        scroll_count = 0
        while scroll_count < 15: # Safety limit
            page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                print("Reached bottom of page.")
                break
            last_height = new_height
            scroll_count += 1
            print(f"Scrolled {scroll_count} times...")
            
        soup = BeautifulSoup(page.content(), 'html.parser')
        final_links = set([a['href'] for a in soup.select('a[href^="/avantajlar/"]') if a['href'] != '/avantajlar/'])
        print(f"Final unique campaign links found after scrolling: {len(final_links)}")
        
        # Test fetching one detail page to verify structure
        if len(final_links) > 0:
            test_target = list(final_links)[0]
            if not test_target.startswith('http'):
                test_target = f"https://param.com.tr{test_target}"
                
            print(f"\nTesting detailed fetch for: {test_target}")
            page.goto(test_target, wait_until="domcontentloaded", timeout=60000)
            time.sleep(2)
            
            detail_soup = BeautifulSoup(page.content(), 'html.parser')
            h1 = detail_soup.find('h1')
            print(f"Title: {h1.text.strip() if h1 else 'N/A'}")
            
            print("Extracting list items (conditions):")
            for ul in detail_soup.find_all('ul'):
                text = ul.text.strip().lower()
                if '%' in text or 'tl' in text or 'geçerli' in text or 'kampanya' in text:
                    for li in ul.find_all('li')[:3]: # First 3 conditions to test
                        print(f" - {li.text.strip()}")
        
        browser.close()

if __name__ == "__main__":
    test_param()
