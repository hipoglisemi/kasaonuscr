import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import text
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))
from database import get_db_session
from models import Campaign

load_dotenv('.env')

def cleanup_campaigns():
    """
    Cleans up expired campaigns:
    Immediately deletes campaigns where end_date is in the past.
    """
    print(f"🧹 Starting Campaign Cleanup: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with get_db_session() as db:
        today = datetime.now().date()
        
        # Immediate deletion of expired campaigns
        to_delete = db.query(Campaign).filter(
            Campaign.end_date < today
        ).all()
        
        if to_delete:
            count = len(to_delete)
            print(f"🗑️ Found {count} expired campaigns to delete (ended before {today}).")
            
            # Use raw SQL for bulk deletion to handle associations if needed, 
            # or rely on relationship cascades if configured correctly.
            # Our Campaign model has cascades for brands, so direct delete should work.
            for c in to_delete:
                db.delete(c)
            
            db.commit()
            print(f"✅ Successfully deleted {count} expired campaigns.")
        else:
            print("✅ No expired campaigns to delete.")
            
    print("🏁 Cleanup completed!")

if __name__ == "__main__":
    cleanup_campaigns()
