
from src.database import get_db_session
from src.models import Bank, Card
from sqlalchemy.orm import joinedload

def list_cards():
    db = get_db_session()
    try:
        banks = db.query(Bank).options(joinedload(Bank.cards)).order_by(Bank.name).all()
        
        print(f"{'BANK':<20} | {'ID':<5} | {'CARD NAME':<30} | {'SLUG':<30}")
        print("-" * 90)
        
        for bank in banks:
            for card in bank.cards:
                print(f"{bank.name[:20]:<20} | {card.id:<5} | {card.name[:30]:<30} | {card.slug[:30]:<30}")
    finally:
        db.close()

if __name__ == "__main__":
    list_cards()
