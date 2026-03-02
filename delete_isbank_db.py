import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# We need to make sure we use psycopg2 directly for raw SQL
def delete_campaigns():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("No DATABASE_URL found.")
        return
        
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Isbankasi Card IDs: 46 (Maximum), 47 (Maximiles), 48 (Genç)
        # Delete related campaign_brands first due to fast constraints
        cur.execute("DELETE FROM campaign_brands WHERE campaign_id IN (SELECT id FROM campaigns WHERE card_id IN (46, 47, 48));")
        deleted_links = cur.rowcount
        print(f"Deleted {deleted_links} campaign_brands records for Isbankasi.")
        
        cur.execute("DELETE FROM campaigns WHERE card_id IN (46, 47, 48);")
        deleted_camps = cur.rowcount
        print(f"Deleted {deleted_camps} Isbankasi campaigns from the database.")
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == "__main__":
    delete_campaigns()
