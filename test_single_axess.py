#!/usr/bin/env python
"""
Quick test to verify participation and eligible_cards are now saved correctly
"""
from src.scrapers.akbank_axess import AkbankAxessScraper
from src.database import get_db_session
from src.models import Campaign

# Clear existing test data
with get_db_session() as db:
    test_campaign = db.query(Campaign).filter(
        Campaign.title.like("%Giyim%")
    ).first()
    if test_campaign:
        db.delete(test_campaign)
        db.commit()
        print("🧹 Cleared existing test campaign")

# Run scraper for just 1 campaign
scraper = AkbankAxessScraper()
urls = scraper._fetch_campaign_list()
if urls:
    print(f"\n🔍 Testing with first campaign: {urls[0]}")
    scraper._process_campaign(urls[0])
    
    # Verify the saved data
    with get_db_session() as db:
        campaign = db.query(Campaign).order_by(Campaign.id.desc()).first()
        if campaign:
            print(f"\n✅ Campaign saved: {campaign.title}")
            print(f"\n📋 Conditions:\n{campaign.conditions[:500]}...")
            print(f"\n🎴 Eligible Cards: {campaign.eligible_cards}")
        else:
            print("❌ No campaign found")
