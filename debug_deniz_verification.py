
import subprocess
import os
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:WnQNWkuA52DaZoaTsGm6gCCqTgk03W9PXsFIWsc77NhTAGwZID3wqOel58mkOdW1@46.225.74.97:5432/postgres"

def check_db():
    print("--- 📊 DB CHECK ---")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT count(*) FROM campaigns WHERE tracking_url LIKE '%denizbonus%'"))
            count = result.scalar()
            print(f"Denizbank Campaigns in DB: {count}")
            
            result_names = conn.execute(text("SELECT title FROM campaigns WHERE tracking_url LIKE '%denizbonus%' LIMIT 5"))
            for r in result_names:
                print(f" - {r[0]}")
    except Exception as e:
        print(f"DB Error: {e}")

def check_curl():
    print("\n--- 🌐 CURL CHECK ---")
    url = "https://www.denizbonus.com/kampanyalar/denizbank-troy-kartinizla-ramazan-alisverislerinize-yuzde10-indirim"
    cmd = [
        "curl", "-L", "-s",
        "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "--max-time", "15", # Short timeout for debug
        url
    ]
    try:
        print(f"Running curl for: {url}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if result.returncode == 0 and result.stdout:
            print(f"✅ Curl Success! Length: {len(result.stdout)}")
            print(f"Snippet: {result.stdout[:200]}")
        else:
            print(f"❌ Curl Failed. ReturnCode: {result.returncode}")
            print(f"Stderr: {result.stderr}")
    except Exception as e:
        print(f"❌ Curl Exception: {e}")

if __name__ == "__main__":
    check_db()
    check_curl()
