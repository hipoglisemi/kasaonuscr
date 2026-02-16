
import sys
import os
from sqlalchemy import create_engine, text
from src.database import get_db_session
from src.models import Campaign, Card

def check_bonus_dates():
    print("🔍 Checking stored dates for Garanti Bonus campaigns...")
    with get_db_session() as db:
        # Find Garanti Bonus card
        card = db.query(Card).filter(Card.name.like("%Bonus%")).first()
        if not card:
            print("❌ Card not found")
            return

        print(f"💳 Checking card: {card.name} (ID: {card.id})")
        
        # Get last 10 campaigns
        campaigns = db.query(Campaign).filter(Campaign.card_id == card.id).order_by(Campaign.created_at.desc()).limit(10).all()
        
        print("\n📅 Last 10 Campaigns:")
        print(f"{'Title':<50} | {'Start Date':<12} | {'End Date':<12}")
        print("-" * 80)
        
        for c in campaigns:
            s_val = c.start_date
            e_val = c.end_date
            
            s_date = str(s_val.date()) if hasattr(s_val, 'date') else str(s_val) if s_val else "NONE"
            e_date = str(e_val.date()) if hasattr(e_val, 'date') else str(e_val) if e_val else "NONE"
            
            print(f"{c.title[:48]:<50} | {s_date:<12} | {e_date:<12}")

if __name__ == "__main__":
    check_bonus_dates()
