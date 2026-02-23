import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL)

def clean_tf_campaigns():
    with engine.begin() as conn:
        # Get Bank ID
        bank = conn.execute(text("SELECT id FROM banks WHERE slug = 'turkiye-finans'")).fetchone()
        if not bank:
            print("Bank 'turkiye-finans' not found.")
            return

        bank_id = bank[0]
        print(f"Bank ID: {bank_id}")

        # Get Cards
        cards = conn.execute(text("SELECT id FROM cards WHERE bank_id = :bank_id"), {"bank_id": bank_id}).fetchall()
        card_ids = [c[0] for c in cards]
        print(f"Card IDs: {card_ids}")

        if not card_ids:
            print("No cards found.")
            return

        # Delete Campaigns
        # Convert list to tuple for SQL IN clause
        if len(card_ids) == 1:
            t_cards = f"({card_ids[0]})"
        else:
            t_cards = tuple(card_ids)
        
        # We need to construct the query string manually or use bindparam with expanding=True (but let's keep it simple for now)
        # Using separate deletes or a loop is safer for simple scripts
        
        count = 0
        for cid in card_ids:
            res = conn.execute(text("DELETE FROM campaigns WHERE card_id = :cid"), {"cid": cid})
            count += res.rowcount
        
        print(f"Deleted {count} campaigns for Türkiye Finans.")

if __name__ == "__main__":
    clean_tf_campaigns()
