from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.maximiles.com.tr/kampanyalar")
    # scroll a bit
    for _ in range(5):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        btn = page.query_selector("button:has-text('Daha Fazla'), a.CampAllShow")
        if btn and btn.is_visible():
            try:
                btn.click()
            except:
                pass
    with open("maximiles_full.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    browser.close()
