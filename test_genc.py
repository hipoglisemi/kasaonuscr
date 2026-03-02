import os
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup

def test_genc():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            print("Connected to 9222...")
            if len(browser.contexts) > 0:
                context = browser.contexts[0]
            else:
                context = browser.new_context()
        except:
            browser = p.chromium.launch(headless=True)
            print("Launched headless...")
            context = browser.new_context()
        
        page = context.new_page()
        print("Gidiliyor...")
        page.goto("https://www.maximumgenc.com.tr/kampanyalar", wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)
        
        # Scroll 5 times
        for _ in range(5):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            btn = page.query_selector(".show-more-opportunity")
            if btn and btn.is_visible():
                print("Daha fazla göster tıklandı.")
                try:
                    btn.click()
                except:
                    page.evaluate("element => element.click()", btn)
                time.sleep(3)
        
        content = page.content()
        soup = BeautifulSoup(content, "html.parser")
        links = soup.find_all("a", href=True)
        
        print(f"Toplam a elementi: {len(links)}")
        
        count = 0
        for a in links:
            href = a["href"]
            if "kampanyalar" in href.lower() and len(href)>15:
                # Basic check
                full_url = urljoin("https://www.maximumgenc.com.tr", a["href"])
                print(f"BULUNDU: {full_url}")
                count += 1
                
        print(f"TOPLAM KAMPANYA LINKI IHTIMALi: {count}")
        page.close()

test_genc()
