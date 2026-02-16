from src.database import get_db_session
from src.models import Bank, Card

def fix_duplicates():
    with get_db_session() as session:
        # 1. Garanti: Merge ID 28 -> ID 1
        bank_new = session.query(Bank).get(28)
        bank_old = session.query(Bank).get(1)
        
        if bank_new and bank_old:
            print("Merging Garanti (ID 28 -> ID 1)...")
            cards = session.query(Card).filter(Card.bank_id == 28).all()
            for card in cards:
                print(f"   Moving card {card.name} (ID {card.id}) from Bank 28 to 1")
                # Check if card slug exists in target bank to avoid unique constraint
                existing_card = session.query(Card).filter(Card.slug == card.slug, Card.bank_id == 1).first()
                if existing_card:
                    print(f"   ⚠️ Card {card.name} (ID {existing_card.id}) already exists in Bank 1. Deleting duplicate (ID {card.id}).")
                    session.delete(card)
                else:
                    card.bank_id = 1
            
            session.delete(bank_new)
            print("   ✅ Deleted Bank ID 28")
        else:
            print("Skipping Garanti merge (banks not found)")

        # 2. İşbankası: Merge ID 2 -> ID 29
        # (We decided ID 29 'isbankasi' is better than ID 2 'isbank' for consistency with filename)
        isbank_old = session.query(Bank).get(2)
        isbank_new = session.query(Bank).get(29)
        
        if isbank_old and isbank_new:
            print("Merging İşbankası (ID 2 -> ID 29)...")
            cards = session.query(Card).filter(Card.bank_id == 2).all()
            for card in cards:
                print(f"   Moving card {card.name} (ID {card.id}) from Bank 2 to 29")
                existing_card = session.query(Card).filter(Card.slug == card.slug, Card.bank_id == 29).first()
                if existing_card:
                    print(f"   ⚠️ Card {card.name} (ID {existing_card.id}) already exists in Bank 29. Deleting duplicate (ID {card.id}).")
                    session.delete(card)
                else:
                    card.bank_id = 29
            
            session.delete(isbank_old)
            print("   ✅ Deleted Bank ID 2")
        else:
             print("Skipping İşbankası merge (banks not found)")

        # 3. Clean up duplicate Garanti cards
        # We know IDs 45, 46, 47 are duplicates of 27, 28, 29 created by bad seed run
        # They have 0 campaigns.
        duplicate_card_ids = [45, 46, 47]
        print("Cleaning up duplicate Garanti cards...")
        for cid in duplicate_card_ids:
            card = session.query(Card).get(cid)
            if card:
                if len(card.campaigns) == 0:
                    session.delete(card)
                    print(f"   Deleted unused duplicate card: {card.name} (ID {cid})")
                else:
                    print(f"   ⚠️ Card ID {cid} has campaigns! skipping delete.")
        
        session.commit()
        print("Done.")

if __name__ == "__main__":
    fix_duplicates()
