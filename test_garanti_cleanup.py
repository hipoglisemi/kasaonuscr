
import sys
import os
from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.garanti_bonus import GarantiBonusScraper
from src.database import get_db_session
from src.models import Campaign, Card

def main():
    print("🧪 Testing Garanti Bonus Scraper (Cleanup + 10 campaigns)")
    print("=" * 60)
    
    # 1. Cleanup existing Garanti Bonus campaigns
    print("🧹 Cleaning up existing Garanti Bonus campaigns...")
    with get_db_session() as db:
        # Find Garanti Bonus card
        card = db.query(Card).filter(Card.slug == 'garanti-bonus').first()
        if card:
            # Delete campaigns
            deleted = db.query(Campaign).filter(Campaign.card_id == card.id).delete()
            db.commit()
            print(f"   ✅ Deleted {deleted} campaigns for card: {card.name}")
        else:
            print("   ⚠️ Garanti Bonus card not found, nothing to delete.")
            
    # 2. Run scraper with limit
    print("\n🚀 Running scraper (Limit: 10)...")
    scraper = GarantiBonusScraper()
    
    # Override _fetch_campaign_list to limit to 10
    original_fetch = scraper._fetch_campaign_list
    
    def limited_fetch():
        urls = original_fetch()
        print(f"   📊 Total campaigns available: {len(urls)}")
        print(f"   🎯 Limiting to first 10 for testing...")
        return urls[:10]
    
    scraper._fetch_campaign_list = limited_fetch
    
    # Run scraper
    scraper.run()
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")

if __name__ == "__main__":
    main()
