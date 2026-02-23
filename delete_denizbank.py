import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    exit(1)

engine = create_engine(DATABASE_URL)

try:
    with engine.begin() as conn:
        print("🗑️ Deleting all DenizBonus campaigns...")
        result = conn.execute(text("DELETE FROM campaigns WHERE tracking_url LIKE '%denizbonus.com%'"))
        print(f"✅ Deleted {result.rowcount} campaigns.")
except Exception as e:
    print(f"❌ Error: {e}")
