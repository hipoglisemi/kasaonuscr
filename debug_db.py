import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
print(f"Connecting to: {db_url[:20]}...")
try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM cards;")
    count = cur.fetchone()[0]
    print(f"Total cards in DB: {count}")
    
    cur.execute("SELECT id, name FROM banks WHERE name ILIKE '%İş%';")
    banks = cur.fetchall()
    print(f"Banks found: {banks}")
    
    if banks:
        bank_id = banks[0][0]
        cur.execute(f"SELECT id, name FROM cards WHERE bank_id = {bank_id};")
        cards = cur.fetchall()
        print(f"Cards for bank {bank_id}: {cards}")
        
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
