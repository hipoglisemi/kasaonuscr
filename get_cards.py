import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT id, name, slug FROM cards WHERE bank_id = 29;")
    rows = cur.fetchall()
    for r in rows:
        print(f"ID {r[0]}: {r[1]} ({r[2]})")
    cur.close()
    conn.close()
except Exception as e:
    print(e)
