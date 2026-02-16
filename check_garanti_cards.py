from src.database import get_db_session
from src.models import Card

def list_garanti_cards():
    with get_db_session() as session:
        cards = session.query(Card).filter(Card.bank_id == 1).all()
        print(f"Total Cards for Garanti (ID 1): {len(cards)}")
        print("-" * 60)
        print(f"{'ID':<5} {'Name':<20} {'Slug':<30} {'Campaigns':<10}")
        print("-" * 60)
        for card in cards:
            campaign_count = len(card.campaigns)
            print(f"{card.id:<5} {card.name:<20} {card.slug:<30} {campaign_count:<10}")

if __name__ == "__main__":
    list_garanti_cards()
