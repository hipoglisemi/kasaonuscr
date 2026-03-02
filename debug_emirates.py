from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

def save_html(url):
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            context = browser.contexts[0] if len(browser.contexts) > 0 else browser.new_context()
        except:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()

        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Scroll
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)
        
        content = page.content()
        soup = BeautifulSoup(content, "html.parser")
        
        with open("emirates_debug.html", "w") as f:
            f.write(soup.prettify())
        
        print(f"Saved HTML to emirates_debug.html")
        page.close()

if __name__ == "__main__":
    url = "https://www.maximiles.com.tr/kampanyalar/maximiles-black-ile-emiratesten-alacaginiz-ucak-biletlerinde-300-usdye-varan-indirim-ayricaligi"
    save_html(url)
