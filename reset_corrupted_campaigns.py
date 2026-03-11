import os
import re
from sqlalchemy import create_engine, MetaData, Table, text
from dotenv import load_dotenv

load_dotenv('.env')
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def reset_and_clean_corrupted():
    """
    Identifies 1629+ corrupted campaigns (with comma-separated characters)
    and resets their auto_corrected flag plus cleans their content fields 
    so the AutoFixer can repair them from fresh source HTML.
    """
    print("🚀 Starting Mass Reset of Corrupted Campaigns...")
    
    with engine.begin() as conn:
        # Prisma names map to underscore in Postgres (auto_corrected -> auto_corrected, rewardText -> reward_text)
        find_query = text("""
            SELECT id FROM campaigns 
            WHERE (
                conditions LIKE '%, %, %' OR 
                eligible_cards LIKE '%, %, %' OR
                description LIKE '%, %, %' OR
                reward_text LIKE '%, %, %'
            )
        """)
        
        results = conn.execute(find_query).fetchall()
        corrupted_ids = [row.id for row in results]
        
        print(f"🔍 Found {len(corrupted_ids)} campaigns with severe character-level corruption.")
        
        if not corrupted_ids:
            print("✨ No corrupted campaigns found with that specific pattern. Checking for auto_corrected items to reset anyway...")
            # We still need to reset the 1809 auto_corrected ones so they get re-checked
            conn.execute(text("UPDATE campaigns SET auto_corrected = False WHERE auto_corrected = True"))
            print("✅ Reset all 1809 'auto_corrected' flags to False.")
            return

        # 2. Perform Mass Reset and Clean
        print(f"🧹 Resetting 'auto_corrected' status and cleaning text fields for {len(corrupted_ids)} campaigns...")
        
        clean_query = text("""
            UPDATE campaigns 
            SET 
                auto_corrected = False,
                conditions = '',
                eligible_cards = '',
                reward_text = 'Detayları İnceleyin',
                description = CASE WHEN length(description) < 100 OR description LIKE '%, %, %' THEN '' ELSE description END
            WHERE id = ANY(:ids)
        """)
        
        result = conn.execute(clean_query, {"ids": corrupted_ids})
        
        print(f"✅ Successfully reset and cleaned {result.rowcount} campaigns.")
        print("🚀 System is now ready for 'python3 data_quality_autofix.py'.")

if __name__ == "__main__":
    confirm = input(f"This will wipe corrupted text of 1600+ campaigns and allow re-scraping. Proceed? (y/n): ")
    if confirm.lower() == 'y':
        reset_and_clean_corrupted()
    else:
        print("Aborted.")
