import sys
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = current_dir
sys.path.insert(0, project_root)
sys.path.insert(1, os.path.join(project_root, "src"))

from src.scrapers.isbankasi_maximum import IsbankMaximumScraper

def main():
    scraper = IsbankMaximumScraper()
    scraper._start_browser()
    
    urls = [
        "https://www.maximum.com.tr/kampanyalar/maximum-ile-yurtici-ucak-biletlerinde-taksit-firsati-etsde",
        "https://www.maximum.com.tr/kampanyalar/is-bankasi-troy-kart-sahipleri-ramazan-ayina-ozel-market-alisverislerinde-maxipuan-kazaniyor"
    ]
    
    try:
        for url in urls:
            print(f"\nURL: {url}")
            scraper.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            soup = BeautifulSoup(scraper.page.content(), "html.parser")
            
            title_el = soup.select_one("h1.gradient-title-text") or soup.find("h1")
            title = scraper._clean(title_el.text) if title_el else "Başlık Yok"
            print(f"Title: {title}")
            
            date_text = ""
            for sel in ["span[id$='KampanyaTarihleri']", ".campaign-date", ".date"]:
                el = soup.select_one(sel)
                if el:
                    date_text = scraper._clean(el.text)
                    print(f"Selector matching date: {sel}")
                    break
            
            print(f"Raw Date Text: '{date_text}'")
            end_iso = scraper._parse_date(date_text, is_end=True)
            print(f"Parsed End ISO: {end_iso}")
            
            if end_iso:
                end_dt = datetime.strptime(end_iso, "%Y-%m-%d")
                print(f"Parsed End Datetime: {end_dt}")
                print(f"Current Datetime: {datetime.now()}")
                if end_dt < datetime.now():
                    print("Status: EXPIRED")
                else:
                    print("Status: VALID")
            else:
                print("Status: COULD NOT PARSE DATE")
            
    finally:
        scraper._stop_browser()

if __name__ == "__main__":
    main()
