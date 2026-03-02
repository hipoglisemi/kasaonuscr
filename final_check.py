import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    # Check the specific Emirates campaign first
    cur.execute("SELECT id, title, length(description) as d_len, length(conditions) as c_len FROM campaigns WHERE title ILIKE '%emirates%' ORDER BY id DESC LIMIT 1;")
    row = cur.fetchone()
    if row:
        print(f"Emirates - ID: {row[0]}, Desc Len: {row[2]}, Cond Len: {row[3]}")
    
    # Check Troy campaign
    cur.execute("SELECT id, title, length(description) as d_len, length(conditions) as c_len FROM campaigns WHERE title ILIKE '%troy%' ORDER BY id DESC LIMIT 1;")
    row = cur.fetchone()
    if row:
        print(f"Troy - ID: {row[0]}, Desc Len: {row[2]}, Cond Len: {row[3]}")
        
    cur.close()
    conn.close()
except Exception as e:
    print(e)
