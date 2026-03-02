from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.maximumgenc.com.tr/kampanyalar", wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)
        print("DOM Loaded")
        
        # Click show more 5 times
        for _ in range(5):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            btn = page.query_selector(".show-more-opportunity")
            if btn and btn.is_visible():
                try:
                    btn.click()
                except:
                    page.evaluate("element => element.click()", btn)
                time.sleep(2)
        
        soup = BeautifulSoup(page.content(), "html.parser")
        items = soup.find_all("div", class_="item")
        print(f"Num items found: {len(items)}")
        
        count = 0
        for item in items:
            a_tag = item.find("a", href=True)
            if a_tag:
                href = a_tag["href"]
                # some items are "Tüm Kampanyalar", ignore
                if "tum-kampanya" not in href and "/kampanyalar/" not in href:
                    print(f"CAMP: {urljoin('https://www.maximumgenc.com.tr', href)}")
                    count += 1
        
        print(f"Total campaigns: {count}")
        browser.close()

if __name__ == "__main__":
    test()
