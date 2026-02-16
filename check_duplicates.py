#!/usr/bin/env python3
"""
Check for duplicate campaign IDs
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.database import get_db_session
from src.models import Campaign
from sqlalchemy import func

def check_duplicates():
    session = get_db_session()
    
    try:
        # Check for duplicate IDs
        duplicates = session.query(
            Campaign.id,
            func.count(Campaign.id).label('count')
        ).group_by(
            Campaign.id
        ).having(
            func.count(Campaign.id) > 1
        ).all()
        
        if duplicates:
            print(f"❌ Found {len(duplicates)} duplicate IDs:")
            for id, count in duplicates:
                print(f"   ID {id}: {count} times")
        else:
            print("✅ No duplicate IDs found")
        
        # Check for duplicate slugs
        dup_slugs = session.query(
            Campaign.slug,
            func.count(Campaign.slug).label('count')
        ).group_by(
            Campaign.slug
        ).having(
            func.count(Campaign.slug) > 1
        ).all()
        
        if dup_slugs:
            print(f"\n⚠️  Found {len(dup_slugs)} duplicate slugs:")
            for slug, count in dup_slugs[:10]:
                print(f"   {slug}: {count} times")
                # Show campaigns with this slug
                campaigns = session.query(Campaign).filter(Campaign.slug == slug).all()
                for c in campaigns:
                    print(f"      - ID {c.id}: {c.title[:50]}")
        else:
            print("\n✅ No duplicate slugs found")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        session.close()

if __name__ == "__main__":
    check_duplicates()
