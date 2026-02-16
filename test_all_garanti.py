
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.scrapers.garanti_bonus import GarantiBonusScraper
from src.scrapers.garanti_milesandsmiles import GarantiMilesAndSmilesScraper
from src.scrapers.garanti_shopandfly import GarantiShopAndFlyScraper
from src.utils.cache_manager import clear_cache

def test_all_garanti_scrapers():
    print("🧪 Testing ALL Garanti Scrapers (Limit: 5 each)")
    print("=" * 60)
    
    # 1. Bonus Scraper
    print("\n🎁 Testing Bonus Scraper...")
    try:
        bonus_scraper = GarantiBonusScraper()
        # Limit to 5
        original_fetch_bonus = bonus_scraper._fetch_campaign_list
        def limited_fetch_bonus():
            urls = original_fetch_bonus()
            return urls[:5]
        bonus_scraper._fetch_campaign_list = limited_fetch_bonus
        bonus_scraper.run()
    except Exception as e:
        print(f"❌ Bonus Failed: {e}")

    # 2. Miles&Smiles Scraper
    print("\n✈️ Testing Miles&Smiles Scraper...")
    try:
        ms_scraper = GarantiMilesAndSmilesScraper()
        # Limit to 5
        original_fetch_ms = ms_scraper._fetch_campaign_list
        def limited_fetch_ms():
            urls = original_fetch_ms()
            return urls[:5]
        ms_scraper._fetch_campaign_list = limited_fetch_ms
        ms_scraper.run()
    except Exception as e:
        print(f"❌ Miles&Smiles Failed: {e}")

    # 3. Shop&Fly Scraper
    print("\n🛍️ Testing Shop&Fly Scraper...")
    try:
        sf_scraper = GarantiShopAndFlyScraper()
        # Limit to 5
        original_fetch_sf = sf_scraper._fetch_campaign_list
        def limited_fetch_sf():
            urls = original_fetch_sf()
            return urls[:5]
        sf_scraper._fetch_campaign_list = limited_fetch_sf
        sf_scraper.run()
    except Exception as e:
        print(f"❌ Shop&Fly Failed: {e}")

    print("\n✅ All Tests Complete")

if __name__ == "__main__":
    test_all_garanti_scrapers()
