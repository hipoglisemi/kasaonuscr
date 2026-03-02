import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT title, description, conditions FROM campaigns WHERE title ILIKE '%emirates%' ORDER BY id DESC LIMIT 1;")
    row = cur.fetchone()
    if row:
        print(f"TITLE: {row[0]}")
        print(f"DESCRIPTION:\n{row[1]}")
        print(f"\nCONDITIONS:\n{row[2]}")
    cur.close()
    conn.close()
except Exception as e:
    print(e)
