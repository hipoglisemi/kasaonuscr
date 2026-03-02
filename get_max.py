import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT id, title, tracking_url FROM campaigns WHERE title ILIKE '%emirates%' ORDER BY id DESC LIMIT 5;")
    rows = cur.fetchall()
    print("Emirates links:")
    for r in rows:
        print(f"ID {r[0]}: {r[1]} -> {r[2]}")
        
    cur.execute("SELECT id, title, tracking_url, card_id FROM campaigns ORDER BY id DESC LIMIT 10;")
    rows = cur.fetchall()
    print("\nRecent 10 links:")
    for r in rows:
        print(f"ID {r[0]} (Card {r[3]}): {r[1]} -> {r[2]}")
    cur.close()
    conn.close()
except Exception as e:
    print(e)
