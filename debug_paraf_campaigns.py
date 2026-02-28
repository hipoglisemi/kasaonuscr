
from src.database import get_db_session
from src.models import Campaign, Card, Bank
from sqlalchemy import or_

def find_paraf_campaigns():
    db = get_db_session()
    try:
        print(f"{'CAMP ID':<10} | {'CARD':<30} | {'BANK':<20} | {'TITLE':<50}")
        print("-" * 120)
        
        camps = db.query(Campaign, Card, Bank).join(Card, Campaign.card_id == Card.id).join(Bank, Card.bank_id == Bank.id).filter(
            or_(
                Campaign.title.ilike('%paraf%'),
                Campaign.description.ilike('%paraf%'),
                Campaign.conditions.ilike('%paraf%')
            )
        ).all()
        
        for camp, card, bank in camps:
            print(f"{camp.id:<10} | {card.name:<30} | {bank.name:<20} | {camp.title[:50]:<50}")
            
        print(f"\nTotal Paraf-related campaigns: {len(camps)}")
        
    finally:
        db.close()

if __name__ == "__main__":
    find_paraf_campaigns()
