import os
import sys
from collections import defaultdict
from sqlalchemy.orm import Session
from src.database import get_db_session
from src.models import Campaign, CampaignBrand

def remove_duplicates():
    print("🧹 Starting Database Cleanup for Duplicate Campaigns...")
    
    deleted_count = 0
    with get_db_session() as db:
        try:
            # 1. Fetch all active campaigns with a tracking URL
            all_campaigns = db.query(Campaign).filter(Campaign.tracking_url.isnot(None)).all()
            
            # 2. Group campaigns by tracking_url
            url_map = defaultdict(list)
            for c in all_campaigns:
                url_map[c.tracking_url].append(c)
                
            # 3. Find and eliminate duplicates
            for url, camps in url_map.items():
                if len(camps) > 1:
                    print(f"\n🔍 Found Duplicate URL: {url}")
                    # Sort campaigns by created_at ascending (keep the oldest, delete the newer ones)
                    camps.sort(key=lambda x: x.created_at)
                    
                    original_campaign = camps[0]
                    duplicates_to_delete = camps[1:]
                    
                    print(f"   👑 Keeping Original ID: {original_campaign.id} (Created: {original_campaign.created_at})")
                    
                    for dup in duplicates_to_delete:
                        print(f"   🗑️ Deleting Duplicate ID: {dup.id} (Created: {dup.created_at})")
                        
                        # Note: SQLAlchemy takes care of CampaignBrand rows automatically 
                        # because we have cascade="all, delete-orphan" on Campaign.brands
                        db.delete(dup)
                        deleted_count += 1
                        
            # 4. Commit changes
            if deleted_count > 0:
                db.commit()
                print(f"✅ Successfully deleted {deleted_count} duplicate campaigns from the database.")
            else:
                print("✨ No duplicates found. Database is clean!")
                
        except Exception as e:
            db.rollback()
            print(f"❌ Error during cleanup: {e}")

if __name__ == "__main__":
    remove_duplicates()
