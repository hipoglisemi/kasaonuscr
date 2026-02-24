"""
Campaign Archiving Script

This script handles the lifecycle of expired campaigns:
1. SOFT DELETE: Sets is_active=False for campaigns where end_date < TODAY
2. HARD DELETE: Permanently deletes campaigns where end_date < TODAY - 10 DAYS

This is designed to run daily via GitHub Actions.
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import sessionmaker

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import Campaign
from src.database import DATABASE_URL, engine, get_db_session

def archive_campaigns():
    print(f"🚀 Starting campaign archiving process...")
    today = datetime.utcnow().date()
    # 10 days threshold for hard deletion (as requested by SEO strategy)
    hard_delete_threshold = today - timedelta(days=10)
    
    print(f"   📅 Today: {today}")
    print(f"   🗑️ Hard Delete Threshold: {hard_delete_threshold}")
    
    try:
        with get_db_session() as db:
            # ---------------------------------------------------------
            # 1. HARD DELETE: Campaigns older than 10 days
            # ---------------------------------------------------------
            print("\n🔍 1. Identifying campaigns to permanently delete (> 10 days expired)...")
            
            # Find campaigns to delete
            to_delete = db.query(Campaign).filter(
                Campaign.end_date != None,
                Campaign.end_date < hard_delete_threshold
            ).all()
            
            deleted_count = 0
            for campaign in to_delete:
                print(f"   ❌ Deleting: [{campaign.id}] {campaign.title[:50]}... (Ended: {campaign.end_date.date()})")
                db.delete(campaign)
                deleted_count += 1
                
            db.commit()
            print(f"✅ Successfully deleted {deleted_count} very old campaigns.")
            
            # ---------------------------------------------------------
            # 2. SOFT DELETE: Campaigns that expired today/recently
            # ---------------------------------------------------------
            print("\n🔍 2. Identifying campaigns to archive (expired recently but < 10 days)...")
            
            # Find active campaigns that have passed their end date
            to_archive = db.query(Campaign).filter(
                Campaign.is_active == True,
                Campaign.end_date != None,
                Campaign.end_date < today
            ).all()
            
            archived_count = 0
            for campaign in to_archive:
                print(f"   📦 Archiving: [{campaign.id}] {campaign.title[:50]}... (Ended: {campaign.end_date.date()})")
                campaign.is_active = False
                archived_count += 1
                
            db.commit()
            print(f"✅ Successfully archived {archived_count} recently expired campaigns.")
            
            print("\n🏁 Archiving process completed successfully!")
            
    except Exception as e:
        print(f"\n📛 CRITICAL ERROR during archiving: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    archive_campaigns()
