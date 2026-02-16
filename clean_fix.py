import os
import sys

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
    
from src.database import get_db_session
from src.models import Campaign

try:
    print("🧹 Cleaning up invalid category campaigns...")
    db = get_db_session()
    
    # Delete specific IDs
    ids_to_delete = [724, 725, 726, 727]
    deleted = db.query(Campaign).filter(Campaign.id.in_(ids_to_delete)).delete(synchronize_session=False)
    db.commit()
    
    print(f"✅ Deleted {deleted} campaigns.")
    db.close()

except Exception as e:
    print(f"❌ Error: {e}")
