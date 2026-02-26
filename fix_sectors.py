import os
import sys
from sqlalchemy.orm import Session
from src.database import get_db_session
from src.models import Campaign, Sector

# Eşleşme (Mapping) Sözlüğü: Hatalı Sektör ID -> Doğru Sektör ID
# Market (127)      -> Market & Gıda (1)
# Giyim (128)       -> Giyim & Aksesuar (3)
# Restoran (129)    -> Restoran & Kafe (4)
# Seyahat (130)     -> Turizm & Konaklama (16)
# Sağlık (131)      -> Kozmetik & Sağlık (7)

SECTOR_MAPPING = {
    127: 1,
    128: 3,
    129: 4,
    130: 16,
    131: 7
}

def fix_duplicate_sectors():
    print("🧹 Starting Database Cleanup for Duplicate Sectors...")
    
    with get_db_session() as db:
        try:
            total_campaigns_moved = 0
            
            # Step 1: Kampanyaları doğru (orijinal 18) sektöre taşı
            for old_sector_id, new_sector_id in SECTOR_MAPPING.items():
                # Hatalı sektöre bağlı tüm kampanyaları bul
                campaigns_to_move = db.query(Campaign).filter(Campaign.sector_id == old_sector_id).all()
                count = len(campaigns_to_move)
                
                if count > 0:
                    print(f"🔄 Moving {count} campaigns from Sector ID {old_sector_id} to Sector ID {new_sector_id}")
                    for camp in campaigns_to_move:
                        camp.sector_id = new_sector_id
                        total_campaigns_moved += 1
            
            print(f"✅ Successfully moved {total_campaigns_moved} campaigns to their correct sectors.")
            
            # Step 2: İçi boşalan (kampanyasız) 5 çöp sektörü sil
            sectors_to_delete = db.query(Sector).filter(Sector.id.in_(list(SECTOR_MAPPING.keys()))).all()
            deleted_count = 0
            
            for sec in sectors_to_delete:
                print(f"🗑️ Deleting useless sector: {sec.name} (ID: {sec.id})")
                db.delete(sec)
                deleted_count += 1
                
            # Step 3: Veritabanına kaydet
            db.commit()
            print(f"✅ Successfully deleted {deleted_count} duplicate sectors from the database.")
            print("✨ Database is beautifully clean now!")
                
        except Exception as e:
            db.rollback()
            print(f"❌ Error during sector cleanup: {e}")

if __name__ == "__main__":
    fix_duplicate_sectors()
