
import sys
import os
from sqlalchemy import create_engine, text
from src.database import get_db_session
from src.models import Campaign, Bank, Card

def delete_garanti_campaigns():
    print("🗑️ Deleting all Garanti BBVA campaigns...")
    
    with get_db_session() as db:
        # Find Garanti Bank ID
        bank = db.query(Bank).filter(Bank.name == "Garanti BBVA").first()
        if not bank:
            print("❌ Garanti BBVA bank not found.")
            return

        # Find all cards belonging to Garanti
        cards = db.query(Card).filter(Card.bank_id == bank.id).all()
        card_ids = [card.id for card in cards]
        
        if not card_ids:
            print("⚠️ No Garanti cards found.")
            return

        print(f"💳 Found {len(cards)} Garanti cards: {[c.name for c in cards]}")

        # Delete campaigns for these cards
        deleted_count = db.query(Campaign).filter(Campaign.card_id.in_(card_ids)).delete(synchronize_session=False)
        
        db.commit()
        print(f"✅ Deleted {deleted_count} campaigns.")

if __name__ == "__main__":
    delete_garanti_campaigns()
