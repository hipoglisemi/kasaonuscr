import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv('.env')
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def migrate_participation_data():
    print("🚀 Migrating participation data from ai_marketing_text to participation column...")
    with engine.begin() as conn:
        # Move existing participation instructions to the new dedicated column
        # and clear ai_marketing_text so it can be refilled with actual marketing summaries
        res = conn.execute(text("""
            UPDATE campaigns 
            SET participation = ai_marketing_text, 
                ai_marketing_text = NULL 
            WHERE ai_marketing_text IS NOT NULL 
              AND (participation IS NULL OR participation = '');
        """))
        print(f"✅ Successfully migrated {res.rowcount} rows in campaigns table.")
        
        # Do the same for test_campaigns
        res_test = conn.execute(text("""
            UPDATE test_campaigns 
            SET participation = ai_marketing_text, 
                ai_marketing_text = NULL 
            WHERE ai_marketing_text IS NOT NULL 
              AND (participation IS NULL OR participation = '');
        """))
        print(f"✅ Successfully migrated {res_test.rowcount} rows in test_campaigns table.")

if __name__ == "__main__":
    migrate_participation_data()
