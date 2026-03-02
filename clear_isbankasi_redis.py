import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def deep_clean_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("No DATABASE_URL found.")
        return
        
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # 1. Clear ALL Isbankasi related IDs
        # 46 = Maximum, 47 = Maximiles, 48 = Genç, 24 = Privia, 45=Bankamatik vs.
        # Let's just find ALL cards belonging to bank_id = 29 (Isbankasi)
        
        cur.execute("SELECT id, name FROM cards WHERE bank_id = 29;")
        isbank_cards = cur.fetchall()
        card_ids = [str(c[0]) for c in isbank_cards]
        
        print(f"Isbankasi Cards found: {isbank_cards}")
        
        if not card_ids:
            print("No Isbankasi cards found in DB!")
            return
            
        id_str = ", ".join(card_ids)
        
        # Delete campaign_brands
        cur.execute(f"DELETE FROM campaign_brands WHERE campaign_id IN (SELECT id FROM campaigns WHERE card_id IN ({id_str}));")
        deleted_links = cur.rowcount
        print(f"Deleted {deleted_links} campaign_brands records for Isbankasi.")
        
        # Delete campaigns
        cur.execute(f"DELETE FROM campaigns WHERE card_id IN ({id_str});")
        deleted_camps = cur.rowcount
        print(f"Deleted {deleted_camps} Isbankasi campaigns from the database.")
        
        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == "__main__":
    deep_clean_db()
