from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

with engine.begin() as conn:
    print("🧹 Deleting old Chippin campaigns to fix URL/Slug sync...")
    conn.execute(text("""
        DELETE FROM campaigns 
        WHERE card_id IN (
            SELECT id FROM cards 
            WHERE bank_id = (SELECT id FROM banks WHERE slug='chippin')
        )
    """))
    print("✅ Cleaned.")
