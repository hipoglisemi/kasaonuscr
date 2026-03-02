import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL")
try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT c.id, c.title, k.name FROM campaigns c JOIN cards k ON c.card_id = k.id WHERE k.bank_id = 29;")
    rows = cur.fetchall()
    print(f"Total Isbankasi campaigns left: {len(rows)}")
    for r in rows:
        print(f" - {r[0]}: {r[1][:50]} ({r[2]})")
        
    cur.close()
    conn.close()
except Exception as e:
    print(e)
