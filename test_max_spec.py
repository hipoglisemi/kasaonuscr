import sys
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

urls = [
    "https://www.maximiles.com.tr/kampanyalar/is-bankasi-troy-kart-sahipleri-ramazan-ayina-ozel-market-alisverislerinde-10-maxipuan-kazaniyor",
    "https://www.maximiles.com.tr/kampanyalar/maximiles-black-ile-restoranlarda-20-indirim-ayricaligi",
    "https://www.maximiles.com.tr/kampanyalar/maximiles-black-le-yapacaginiz-otopark-odemelerinizde-50-indirim",
    "https://www.maximiles.com.tr/kampanyalar/maximiles-black-ile-emiratesten-alacaginiz-ucak-biletlerinde-300-usdye-varan-indirim-ayricaligi"
]

def test_maximiles():
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            print("Connected to CDP")
            context = browser.contexts[0] if len(browser.contexts) > 0 else browser.new_context()
        except:
            browser = p.chromium.launch(headless=True)
            print("Launched Headless")
            context = browser.new_context()

        page = context.new_page()
        
        for url in urls:
            print(f"\n======================================")
            print(f"Loading {url}...")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            soup = BeautifulSoup(page.content(), "html.parser")
            
            # Test a bunch of likely content selectors
            classes = [
                ".campaign-detail .page-content",
                ".page-content.campaign-detail",
                ".page-content", 
                "section div.container", 
                ".detail-text", 
                ".campaign-content", 
                ".text-area", 
                ".opportunity-detail", 
                ".campaign-detail-content"
            ]
            
            found = False
            for cls in classes:
                elems = soup.select(cls)
                if elems:
                    for i, elem in enumerate(elems):
                        text = elem.get_text(separator="\n", strip=True)
                        if len(text) > 100:
                            found = True
                            print(f"\n✅ FOUND -> [{cls} - {i}] chars: {len(text)}")
                            print(f"Sample:\n{text[:300]}")
                            print("-" * 30)
            
            if not found:
                print("\n❌ Could not find content with common selectors.")
                # Print the largest div with text to give us a clue
                divs = soup.find_all(["div", "section", "article"])
                largest_elem = None
                max_len = 0
                for elem in divs:
                    text = elem.get_text(separator="\n", strip=True)
                    if len(text) > max_len and len(text) < 15000: # exclude whole body
                        max_len = len(text)
                        largest_elem = elem

                if largest_elem:
                    print(f"Largest element name: {largest_elem.name}, class: {largest_elem.get('class')}")
                    text = largest_elem.get_text(separator='\n', strip=True)
                    print(f"Length: {len(text)}")
                    print(text[:300])
            
        page.close()

if __name__ == "__main__":
    test_maximiles()
