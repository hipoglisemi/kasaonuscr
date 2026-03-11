import os
from sqlalchemy import create_engine, MetaData, Table, text
from dotenv import load_dotenv

load_dotenv('.env')
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)
metadata = MetaData()
metadata.reflect(bind=engine)

table_name = 'test_campaigns' if os.environ.get('TEST_MODE') == '1' else 'campaigns'
campaigns_table = Table(table_name, metadata, autoload_with=engine)

def cleanup_placeholder_campaigns():
    """
    Deletes campaigns that received the 'Kampanya detayları ve tüm koşullar...' placeholder
    so that the scrapers can re-fetch their clean, fresh data from the banks.
    """
    placeholder_text = "Kampanya detayları ve tüm koşullar için lütfen ilgili bankanın kampanya sayfasını ziyaret ediniz."
    
    with engine.begin() as conn:
        # First, find how many we have
        query = campaigns_table.select().where(
            (campaigns_table.c.conditions == placeholder_text) |
            (campaigns_table.c.conditions.like('%Kampanya detayları ve tüm koşullar için%')) |
            (campaigns_table.c.description == placeholder_text)
        )
        
        results = conn.execute(query).fetchall()
        
        print(f"🧹 FOUND {len(results)} corrupted campaigns with generic placeholders.")
        
        if len(results) == 0:
            print("✨ Vay be! Sistemde silinecek hiçbir Placeholder kalmamış.")
            return

        # Prepare IDs to delete
        ids_to_delete = [row.id for row in results]
        
        print(f"🗑️ Deleting {len(ids_to_delete)} campaigns from `{table_name}` table to allow fresh scraping...")
        
        # We need to handle potential foreign key constraints (like campaign_brands)
        # Using raw SQL to delete associated child records first if they exist
        try:
            # Postgres cascading or manual children deletion
            conn.execute(text("DELETE FROM campaign_brands WHERE campaign_id = ANY(:ids)"), {"ids": ids_to_delete})
            
            # Now delete the actual campaigns
            delete_stmt = campaigns_table.delete().where(campaigns_table.c.id.in_(ids_to_delete))
            result = conn.execute(delete_stmt)
            
            print(f"✅ SUCCESSFULLY DELETED {result.rowcount} campaigns.")
            print("🚀 You can now safely run the scrapers again! They will fetch fresh details instead of skipping.")
            
        except Exception as e:
            print(f"❌ Error during deletion: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    confirm = input("Are you sure you want to delete placeholder campaigns so they can be re-scraped? (y/n): ")
    if confirm.lower() == 'y':
        cleanup_placeholder_campaigns()
    else:
        print("Aborted.")
