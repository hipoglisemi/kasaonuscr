
import sys
import os
from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_db_session
from src.models import Campaign

def check_sidebar_data():
    print("🔍 Checking last 5 campaigns for sidebar data...")
    print("=" * 60)
    
    with get_db_session() as db:
        # Get last 10 campaigns sorted by created_at desc
        campaigns = db.query(Campaign).order_by(Campaign.created_at.desc()).limit(10).all()
        
        for c in campaigns:
            print(f"\n📌 Title: {c.title}")
            print(f"   Slug: {c.slug}")
            print("-" * 20)
            
            # Check for specific sidebar keywords
            sidebar_keywords = [
                "KATILMAK İÇİN", "BAŞLANGIÇ", "BİTİŞ", 
                "SMS", "3340", "BonusFlaş", "Geçerlilik"
            ]
            
            found_keywords = []
            
            # Check in conditions
            if c.conditions:
                print(f"   📋 Conditions: {c.conditions[:200].replace(chr(10), ' ')}...")
                for kw in sidebar_keywords:
                    if kw in c.conditions:
                        found_keywords.append(f"conditions: {kw}")
            
            # Check in description
            if c.description:
                print(f"   📝 Description: {c.description[:200].replace(chr(10), ' ')}...")
                for kw in sidebar_keywords:
                    if kw in c.description:
                        found_keywords.append(f"description: {kw}")
            
            if found_keywords:
                print(f"   ✅ Sidebar keywords found: {', '.join(found_keywords)}")
            else:
                print(f"   ⚠️ No keywords found. Check content above.")

if __name__ == "__main__":
    check_sidebar_data()
