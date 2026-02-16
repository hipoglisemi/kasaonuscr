from src.database import get_db_session
from src.models import Bank

def list_banks():
    with get_db_session() as session:
        banks = session.query(Bank).all()
        print(f"Total Banks: {len(banks)}")
        print("-" * 40)
        print(f"{'ID':<5} {'Name':<20} {'Slug':<20}")
        print("-" * 40)
        for bank in banks:
            card_count = len(bank.cards)
            campaign_count = sum(len(c.campaigns) for c in bank.cards)
            print(f"{bank.id:<5} {bank.name:<20} {bank.slug:<20} Cards: {card_count:<5} Campaigns: {campaign_count}")

if __name__ == "__main__":
    list_banks()
