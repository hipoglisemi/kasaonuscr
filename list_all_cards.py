
from src.database import get_db_session
from src.models import Card, Bank

def list_all():
    db = get_db_session()
    try:
        print(f"{'BANK':<20} | {'ID':<5} | {'CARD NAME':<30} | {'SLUG':<30}")
        print("-" * 90)
        
        cards = db.query(Card, Bank).join(Bank, Card.bank_id == Bank.id).order_by(Bank.name, Card.name).all()
        for card, bank in cards:
            print(f"{bank.name:<20} | {card.id:<5} | {card.name:<30} | {card.slug:<30}")
            
    finally:
        db.close()

if __name__ == "__main__":
    list_all()
