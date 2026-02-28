import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.scrapers.enpara import EnparaScraper
from src.scrapers.vakifbank import VakifbankScraper
from src.scrapers.paraf import ParafScraper
from src.scrapers.isbankasi_maximum import IsbankMaximumScraper

def main():
    print("--- ENPARA ---")
    try:
        e = EnparaScraper()
        e_links = e._fetch_campaign_links()
        print(f"Enpara Found: {len(e_links)}")
    except Exception as e:
        print(f"Enpara Error: {e}")

    print("\n--- VAKIFBANK ---")
    try:
        v = VakifbankScraper()
        v_links = v._fetch_campaign_list()
        print(f"Vakifbank Found: {len(v_links)}")
    except Exception as e:
        print(f"Vakifbank Error: {e}")

    print("\n--- PARAF / PARAFLY ---")
    try:
        p = ParafScraper()
        for src in p.SOURCES:
            c = p._fetch_campaigns(src)
            print(f"{src['name']} Found: {len(c)}")
    except Exception as e:
        print(f"Paraf Error: {e}")

    print("\n--- MAXIMUM ---")
    try:
        m = IsbankMaximumScraper()
        # Initialize driver manually to test fetch
        m.driver = m._get_driver()
        m_links = m._fetch_campaign_urls()
        print(f"Maximum Found: {len(m_links)}")
        if m.driver: m.driver.quit()
        if m.display: m.display.stop()
    except Exception as e:
        print(f"Maximum Error: {e}")

if __name__ == '__main__':
    main()
