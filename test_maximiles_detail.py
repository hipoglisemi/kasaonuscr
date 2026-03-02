from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin

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
        
        list_url = "https://www.maximiles.com.tr/kampanyalar"
        print(f"Going to {list_url}")
        page.goto(list_url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)
        soup = BeautifulSoup(page.content(), "html.parser")
        
        campaign_link = None
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "kampanyalar/" not in href and "kredi-karti" not in href and "programi" not in href and href.startswith("/") and len(href) > 20: 
                if "ayricaligi" in href or "firsat" in href or "indirim" in href or "maximil" in href or "-" in href:
                    campaign_link = urljoin("https://www.maximiles.com.tr", href)
                    break
                    
        print(f"Testing real campaign URL: {campaign_link}")
        
        if not campaign_link:
            print("Still no URL found")
            return
            
        try:
            page.goto(campaign_link, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            
            soup = BeautifulSoup(page.content(), "html.parser")
            
            # Look for potential content containers
            potential_classes = [".content-part", ".campaign-content", ".detail-text", ".article-content", ".detail", ".page-content", "div.text", "section.campaign-detail", ".body-text"]
            
            found = False
            for cls in potential_classes:
                elems = soup.select(cls)
                for i, elem in enumerate(elems):
                    text = elem.get_text(separator="\n", strip=True)
                    if len(text) > 50:
                        print(f"\n[{cls} - {i}] chars: {len(text)}")
                        print(f"Sample: {text[:200]}")
                        print("-" * 30)
                        found = True
            
            if not found:
                container = soup.select_one("div.container")
                if container:
                    print("Fallback to container:")
                    print(container.get_text(separator="\n", strip=True)[:500])
                    
        finally:
            page.close()

if __name__ == "__main__":
    test_maximiles()
