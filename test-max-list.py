from playwright.sync_api import sync_playwright
import time
from bs4 import BeautifulSoup

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://www.maximiles.com.tr/kampanyalar")
        print("Scrolling...")
        for _ in range(5):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            btn = page.query_selector("button:has-text('Daha Fazla'), a.CampAllShow")
            if btn and btn.is_visible():
                btn.click()
                time.sleep(3)
        
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        print("Finding links and checking texts...")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/kampanyalar/" in href:
                # check if there's any 'sona' text inside this a tag or its parent
                text = a.get_text(separator=" ", strip=True).lower()
                parent_text = ""
                parent = a.find_parent("div", class_="campaign-card") or a.find_parent("div", class_="opportunity-result") or a.find_parent("div", class_="card") or a.parent
                if parent:
                     parent_text = parent.get_text(separator=" ", strip=True).lower()
                     
                if "sona ermiştir" in text or "bitmiş" in text or "sona ermiştir" in parent_text or "bitmiş" in parent_text or "sona erdi" in text or "sona erdi" in parent_text:
                    print(f"EXPIRED LINK FOUND: {href}")
                    print(f"Parent Text snippet: {parent_text[:100]}...")
        browser.close()

if __name__ == "__main__":
    main()
