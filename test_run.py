
import sys
import os
sys.path.append(os.getcwd())

try:
    from src.scrapers.vakifbank import VakifbankScraper
    print("✅ Successfully imported VakifbankScraper")
    scraper = VakifbankScraper()
    print("✅ Initialized Scraper")
except Exception as e:
    print(f"❌ Error: {e}")
