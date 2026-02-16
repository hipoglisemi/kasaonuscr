import os
import sys

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
    
from src.database import get_db_session
from src.models import Campaign

try:
    print("🔍 Inspecting Recent Campaigns...")
    db = get_db_session()
    
    # Get last 5 campaigns
    campaigns = db.query(Campaign).order_by(Campaign.created_at.desc()).limit(5).all()
    
    for c in campaigns:
        print("\n" + "="*50)
        print(f"🆔 ID: {c.id}")
        print(f"📌 Title: {c.title}")
        print(f"🔗 Slug: {c.slug}")
        print(f"📅 Start: {c.start_date} | End: {c.end_date}")
        print("-" * 20)
        print(f"📝 DESCRIPTION:\n{c.description}")
        print("-" * 20)
        print(f"📋 CONDITIONS:\n{c.conditions}")
        print("-" * 20)
        
        # Check specific fixes
        if "Geçerli Kartlar" in c.conditions:
             print("❌ FAILED: 'Geçerli Kartlar' found in conditions body!")
        else:
             print("✅ PASSED: Conditions cleanly summarized (no card spam).")

        if c.start_date or c.end_date:
             print("✅ PASSED: Dates extracted.")
        else:
             print("⚠️ WARNING: Dates missing.")

        if "KATILIM" in c.conditions:
             print("✅ PASSED: Participation explicitly captured.")
        else:
             print("⚠️ WARNING: Participation keyword missing in conditions.")

    db.close()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
