#!/usr/bin/env python3
"""
Re-scrape with fixed AI parser
Deletes all campaigns and scrapes 10 from each Yapı Kredi scraper
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import get_db_session
from src.models import Campaign

def delete_all_campaigns():
    """Delete all campaigns from database"""
    print("🗑️  Deleting all campaigns from database...\n")
    
    session = get_db_session()
    
    try:
        # Get count
        count = session.query(Campaign).count()
        
        print(f"📊 Found {count} campaigns to delete\n")
        
        if count == 0:
            print("✅ No campaigns to delete!")
            session.close()
            return True
        
        print("⚠️  WARNING: This will delete ALL campaigns!")
        print("   Proceeding in 3 seconds...\n")
        import time
        time.sleep(3)
        
        # Delete all campaigns
        session.query(Campaign).delete()
        session.commit()
        
        print(f"✅ Successfully deleted {count} campaigns!\n")
        session.close()
        return True
    except Exception as e:
        print(f"❌ Error deleting campaigns: {e}")
        session.rollback()
        session.close()
        return False

if __name__ == "__main__":
    delete_all_campaigns()
