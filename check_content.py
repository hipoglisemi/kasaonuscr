import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT id, title, description, conditions, length(description) as d_len FROM campaigns WHERE card_id = 49 ORDER BY id DESC LIMIT 1;")
    row = cur.fetchone()
    if row:
        print(f"ID: {row[0]}")
        print(f"Title: {row[1]}")
        print(f"Description Length: {row[4]}")
        print(f"Description Start: {row[2][:200]}...")
        # Conditions is usually a string in our model
        print(f"Conditions: {row[3][:200]}...")
    else:
        print("No Maximiles campaign found.")
    cur.close()
    conn.close()
except Exception as e:
    print(e)
