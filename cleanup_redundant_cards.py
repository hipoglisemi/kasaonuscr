
from src.database import get_db_session
from src.models import Campaign, Card, Bank
from sqlalchemy import or_

def cleanup_garanti_cards():
    session = get_db_session()
    try:
        # 1. Get Master Cards
        # We need to be careful with IDs as they might vary, so we'll use slugs/names
        master_bonus = session.query(Card).filter(Card.slug == "garanti-bonus").first()
        master_miles = session.query(Card).filter(Card.slug == "garanti-milessmiles").first()
        master_shop = session.query(Card).filter(Card.slug == "garanti-shopandfly").first()
        
        if not all([master_bonus, master_miles, master_shop]):
            print("❌ Master cards not found! Check slugs.")
            return

        print(f"🎯 Master Cards found: Bonus({master_bonus.id}), Miles({master_miles.id}), Shop({master_shop.id})")

        # 2. Identify Redundant Cards for Garanti
        garanti_bank = session.query(Bank).filter(Bank.name == "Garanti BBVA").first()
        if not garanti_bank:
            print("❌ Garanti BBVA bank not found!")
            return

        redundant_cards = session.query(Card).filter(
            Card.bank_id == garanti_bank.id,
            Card.id.notin_([master_bonus.id, master_miles.id, master_shop.id])
        ).all()

        print(f"🔍 Found {len(redundant_cards)} redundant cards for Garanti.")

        total_migrated = 0
        for card in redundant_cards:
            # Determine target master card
            target_id = master_bonus.id # Default to Bonus
            
            name_lower = card.name.lower()
            if "shop" in name_lower or "fly" in name_lower:
                target_id = master_shop.id
            elif "miles" in name_lower or "smiles" in name_lower:
                target_id = master_miles.id
            
            # Migrate campaigns
            campaigns = session.query(Campaign).filter(Campaign.card_id == card.id).all()
            if campaigns:
                print(f"   📦 Migrating {len(campaigns)} campaigns from '{card.name}' (ID: {card.id}) -> Master Card ID: {target_id}")
                for camp in campaigns:
                    camp.card_id = target_id
                total_migrated += len(campaigns)
            
            # Delete redundant card
            print(f"   🗑️  Deleting redundant card: {card.name}")
            session.delete(card)
        
        # --- TEB CLEANUP ---
        teb_master = session.query(Card).filter(Card.slug == "teb-kredi-karti").first()
        if teb_master:
            teb_bank = session.query(Bank).filter(Bank.slug == "teb").first()
            if teb_bank:
                teb_redundant = session.query(Card).filter(
                    Card.bank_id == teb_bank.id,
                    Card.slug.in_(['teb-genel', 'teb-visa'])
                ).all()
                for card in teb_redundant:
                    campaigns = session.query(Campaign).filter(Campaign.card_id == card.id).all()
                    if campaigns:
                        print(f"   📦 Migrating {len(campaigns)} campaigns from '{card.name}' -> '{teb_master.name}'")
                        for camp in campaigns:
                            camp.card_id = teb_master.id
                        total_migrated += len(campaigns)
                    session.delete(card)

        # --- ENPARA CLEANUP ---
        enpara_master = session.query(Card).filter(Card.slug == "enpara-kredi-karti").first()
        if enpara_master:
            enpara_bank = session.query(Bank).filter(Bank.slug == "enpara").first()
            if enpara_bank:
                enpara_redundant = session.query(Card).filter(
                    Card.bank_id == enpara_bank.id,
                    Card.slug == 'enpara-com'
                ).all()
                for card in enpara_redundant:
                    campaigns = session.query(Campaign).filter(Campaign.card_id == card.id).all()
                    if campaigns:
                        print(f"   📦 Migrating {len(campaigns)} campaigns from '{card.name}' -> '{enpara_master.name}'")
                        for camp in campaigns:
                            camp.card_id = enpara_master.id
                        total_migrated += len(campaigns)
                    session.delete(card)

        session.commit()
        print(f"\n✅ Cleanup complete. {total_migrated} campaigns migrated.")

    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    cleanup_garanti_cards()
