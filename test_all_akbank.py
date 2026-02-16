
import sys
import os
from src.database import get_db_session
from src.models import Campaign, Card
from src.scrapers.akbank_axess import AkbankAxessScraper
from src.scrapers.akbank_free import AkbankFreeScraper
from src.scrapers.akbank_business import AkbankBusinessScraper

def clear_akbank_data():
    print("🧹 Cleaning up Akbank data...")
    with get_db_session() as db:
        cards = db.query(Card).filter(Card.name.in_(['Axess', 'Axess Free', 'Axess Business'])).all()
        card_ids = [c.id for c in cards]
        if card_ids:
            deleted = db.query(Campaign).filter(Campaign.card_id.in_(card_ids)).delete(synchronize_session=False)
            db.commit()
            print(f"✅ Deleted {deleted} campaigns.")
        else:
            print("⚠️ No Akbank cards found to clean.")

def test_scraper(scraper_class, name):
    print(f"\n🧪 Testing {name}...")
    scraper = scraper_class()
    
    # Monkey patch fetch to limit only 5
    original_fetch = scraper._fetch_campaign_list
    def limited_fetch():
        urls = original_fetch()
        return urls[:5]
    scraper._fetch_campaign_list = limited_fetch
    
    try:
        scraper.run()
        print(f"✅ {name} finished successfully.")
    except Exception as e:
        print(f"❌ {name} failed: {e}")

if __name__ == "__main__":
    clear_akbank_data()
    
    test_scraper(AkbankAxessScraper, "Axess Scraper")
    test_scraper(AkbankFreeScraper, "Free Scraper")
    test_scraper(AkbankBusinessScraper, "Business Scraper")
    
    print("\n🎉 All Akbank tests completed.")
