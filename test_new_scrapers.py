
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.scrapers.garanti_milesandsmiles import GarantiMilesAndSmilesScraper
from src.scrapers.garanti_shopandfly import GarantiShopAndFlyScraper
from src.utils.cache_manager import clear_cache

def test_scrapers():
    print("🧪 Testing New Garanti Scrapers (Limit: 3 each)")
    print("=" * 60)
    
    # Test Miles&Smiles
    print("\n✈️ Testing Miles&Smiles Scraper...")
    try:
        ms_scraper = GarantiMilesAndSmilesScraper()
        # Monkey patch fetch_campaign_list to limit results
        original_fetch = ms_scraper._fetch_campaign_list
        
        def limited_fetch():
            urls = original_fetch()
            return urls[:3]
            
        ms_scraper._fetch_campaign_list = limited_fetch
        ms_scraper.run()
    except Exception as e:
        print(f"❌ Miles&Smiles Failed: {e}")

    # Test Shop&Fly
    print("\n🛍️ Testing Shop&Fly Scraper...")
    try:
        sf_scraper = GarantiShopAndFlyScraper()
        # Monkey patch fetch_campaign_list to limit results
        original_fetch_sf = sf_scraper._fetch_campaign_list
        
        def limited_fetch_sf():
            urls = original_fetch_sf()
            return urls[:3]
            
        sf_scraper._fetch_campaign_list = limited_fetch_sf
        sf_scraper.run()
    except Exception as e:
        print(f"❌ Shop&Fly Failed: {e}")

    print("\n✅ Test Complete")

if __name__ == "__main__":
    test_scrapers()
