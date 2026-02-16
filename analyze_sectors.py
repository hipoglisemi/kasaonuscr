#!/usr/bin/env python3
"""
Analyze campaigns by sector
Shows how many campaigns are marked as "Diğer" (Other) sector
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import get_db_session
from src.models import Campaign, Sector
from sqlalchemy import func

def analyze_campaigns():
    session = get_db_session()
    
    try:
        # Total campaigns
        total = session.query(Campaign).count()
        print(f"📊 Toplam Kampanya: {total}\n")
        
        # Group by sector
        print("🏷️  Sektör Bazında Dağılım:")
        print("=" * 60)
        
        sector_stats = session.query(
            Sector.name,
            Sector.slug,
            func.count(Campaign.id).label('count')
        ).join(
            Campaign, Campaign.sector_id == Sector.id
        ).group_by(
            Sector.id, Sector.name, Sector.slug
        ).order_by(
            func.count(Campaign.id).desc()
        ).all()
        
        diger_count = 0
        
        for sector_name, sector_slug, count in sector_stats:
            percentage = (count / total * 100) if total > 0 else 0
            icon = "⚠️ " if sector_slug == "diger" else "   "
            print(f"{icon}{sector_name:30} {count:3} kampanya ({percentage:5.1f}%)")
            
            if sector_slug == "diger":
                diger_count = count
        
        # Campaigns without sector
        no_sector = session.query(Campaign).filter(Campaign.sector_id == None).count()
        if no_sector > 0:
            percentage = (no_sector / total * 100) if total > 0 else 0
            print(f"⚠️  Sektör Atanmamış:              {no_sector:3} kampanya ({percentage:5.1f}%)")
        
        print("=" * 60)
        print(f"\n⚠️  'Diğer' Sektörü: {diger_count} kampanya")
        
        if diger_count > 0:
            print(f"\n📋 'Diğer' Sektöründeki Kampanyalar:")
            print("-" * 60)
            
            diger_sector = session.query(Sector).filter(Sector.slug == "diger").first()
            if diger_sector:
                diger_campaigns = session.query(Campaign).filter(
                    Campaign.sector_id == diger_sector.id
                ).limit(20).all()
                
                for i, camp in enumerate(diger_campaigns, 1):
                    print(f"{i:2}. [{camp.card.name}] {camp.title[:70]}")
                
                if diger_count > 20:
                    print(f"\n   ... ve {diger_count - 20} kampanya daha")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        session.close()

if __name__ == "__main__":
    analyze_campaigns()
