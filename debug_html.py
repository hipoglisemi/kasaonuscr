import sys
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

def check_html(url):
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0] if len(browser.contexts) > 0 else browser.new_context()
        except:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()

        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Comprehensive scroll
        page.evaluate("""async () => {
            await new Promise((resolve) => {
                let totalHeight = 0;
                let distance = 200;
                let timer = setInterval(() => {
                    let scrollHeight = document.body.scrollHeight;
                    window.scrollBy(0, distance);
                    totalHeight += distance;
                    if(totalHeight >= scrollHeight){
                        clearInterval(timer);
                        resolve();
                    }
                }, 100);
            });
        }""")
        time.sleep(3)
        
        soup = BeautifulSoup(page.content(), "html.parser")
        
        # Let's find all text blocks and see their classes
        print(f"--- ANALYZING: {url} ---")
        
        # Try finding tables
        tables = soup.find_all("table")
        print(f"Found {len(tables)} tables.")
        for i, t in enumerate(tables):
            txt = t.get_text(separator=" | ", strip=True)
            print(f"Table {i} (len {len(txt)}): {txt[:200]}...")

        # Find divs with decent text
        divs = soup.find_all(["div", "section"])
        for d in divs:
            cls = d.get('class', [])
            txt = d.get_text(strip=True)
            if 300 < len(txt) < 5000:
                # print(f"Div {cls} len {len(txt)}")
                pass
                
        # Specifically check current selectors
        sel = ".page-content, section div.container, .detail-text, .campaign-content, .text-area"
        elems = soup.select(sel)
        print(f"\nSelector matches ({sel}):")
        for i, e in enumerate(elems):
            t = e.get_text(separator="\n", strip=True)
            print(f"Match {i} (len {len(t)}): {t[:100]}...")
            
        page.close()

if __name__ == "__main__":
    urls = [
        "https://www.maximiles.com.tr/kampanyalar/maximiles-black-ile-restoranlarda-20-indirim-ayricaligi",
        "https://www.maximiles.com.tr/kampanyalar/maximiles-black-le-yapacaginiz-otopark-odemelerinizde-50-indirim"
    ]
    for u in urls:
        check_html(u)
        print("-" * 60)
