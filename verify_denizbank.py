import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        print("\n🔍 Verifying last 10 Denizbank campaigns...\n")
        
        result = conn.execute(text("""
            SELECT 
                c.id,
                c.title,
                c.start_date,
                c.end_date,
                c.eligible_cards,
                c.conditions,
                c.updated_at,
                (
                    SELECT string_agg(b.name, ', ')
                    FROM campaign_brands cb
                    JOIN brands b ON cb.brand_id = b.id
                    WHERE cb.campaign_id = c.id
                ) as brand_names,
                c.slug,
                c.is_active
            FROM campaigns c
            WHERE c.updated_at > NOW() - INTERVAL '1 hour'
            ORDER BY c.updated_at DESC
            LIMIT 10
        """))
        
        rows = result.fetchall()
        
        if not rows:
            print("❌ No campaigns found updated in the last hour.")
        
        for row in rows:
            print(f"🆔 ID: {row[0]}")
            print(f"📌 Title: {row[1]}")
            print(f"🔗 Slug: {row[8]}")
            print(f"🟢 Active: {row[9]}")
            print(f"📅 Dates: {row[2]} - {row[3]}")
            print(f"💳 Eligible Cards: {row[4]}")
            
            # Check participation in conditions
            conditions = row[5] or ""
            participation = "N/A"
            for line in conditions.split('\n'):
                if line.startswith("KATILIM:"):
                    participation = line
                    break
            print(f"📲 Participation: {participation}")
            print(f"📝 Conditions Preview:\n{conditions[:500]}...") # Print first 500 chars of conditions
            
            print(f"🕒 Updated: {row[6]}")
            print(f"🏷️ Brands: {row[7]}")
            print("-" * 50)
            
except Exception as e:
    print(f"❌ Error: {e}")
