from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def test_detail():
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            print("Connected to CDP")
            if len(browser.contexts) > 0:
                context = browser.contexts[0]
            else:
                context = browser.new_context()
        except:
            browser = p.chromium.launch(headless=True)
            print("Launched headless")
            context = browser.new_context()
            
        page = context.new_page()
        
        test_url = "https://www.maximumgenc.com.tr/kafe-ve-restoran-harcamalarinda-indirim-firsati"
        print(f"Gidiliyor: {test_url}")
        
        page.goto(test_url, wait_until="domcontentloaded", timeout=60000)
        
        soup = BeautifulSoup(page.content(), "html.parser")
        
        title_elem = soup.select_one("h1.color-purple")
        title = title_elem.text.strip() if title_elem else "Bulunamadi"
        print(f"Baslik: {title}")
        
        content_elem = soup.select_one("div.content-part")
        if content_elem:
            text = content_elem.get_text(separator="\n", strip=True)
            print(f"Icerik Karakter Sayisi: {len(text)}")
            print(f"Icerik (Ilk 200 Karakter):\n{text[:200]}")
            
            # Li ler veya ekstra element var mi?
            lis = content_elem.find_all("li")
            print(f"Icerikte {len(lis)} adet bullet/madde bulundu.")
        else:
            print("Content part BULUNAMADI!!")
            
        page.close()

if __name__ == "__main__":
    test_detail()
