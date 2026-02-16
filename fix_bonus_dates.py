
import sys
import os
from sqlalchemy import create_engine, text
from src.database import get_db_session
from src.models import Campaign, Card
from src.scrapers.garanti_bonus import GarantiBonusScraper

def fix_specific_campaigns():
    print("🔧 Fixing specific Garanti Bonus campaigns...")
    
    with get_db_session() as db:
        # 1. Delete campaigns with missing start_date
        print("🗑️ Deleting campaigns with missing start_date...")
        card = db.query(Card).filter(Card.name.like("%Bonus%")).first()
        if not card:
            print("❌ Card not found")
            return

        affected_rows = db.query(Campaign).filter(
            Campaign.card_id == card.id,
            Campaign.start_date == None
        ).delete(synchronize_session=False)
        
        db.commit()
        print(f"✅ Deleted {affected_rows} stale campaigns.")
        
    # 2. Re-run scraper (limited)
    print("\n🔄 Re-running scraper to fetch fresh data...")
    scraper = GarantiBonusScraper()
    # Limit to 10 to ensure we catch the deleted ones
    original_fetch = scraper._fetch_campaign_list
    def limited_fetch():
        urls = original_fetch()
        return urls[:10]
    scraper._fetch_campaign_list = limited_fetch
    scraper.run()

if __name__ == "__main__":
    fix_specific_campaigns()
