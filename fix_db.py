import os
import re
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv('.env')
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)
metadata = MetaData()
metadata.reflect(bind=engine)

# Get the right table depending on environment
table_name = 'test_campaigns' if os.environ.get('TEST_MODE') == '1' else 'campaigns'
campaigns_table = Table(table_name, metadata, autoload_with=engine)

def is_corrupted(text):
    if not text:
        return False
    pattern = r'(.)\s*,\s*(.)\s*,\s*(.)'
    return bool(re.search(pattern, text))

print("🔍 Veritabanındaki hatalı kampanyalar taranıyor...")

with engine.connect() as conn:
    result = conn.execute(campaigns_table.select())
    campaigns = result.fetchall()
    
    fixed_cards_count = 0
    fixed_conditions_count = 0
    deleted_kuveytturk_imgs_count = 0
    
    for row in campaigns:
        needs_update = False
        update_data = {}
        
        # Check eligible_cards
        if row.eligible_cards and is_corrupted(row.eligible_cards):
            cleaned_cards = "".join([char for char in row.eligible_cards if char not in (',', ' ', '\n')])
            if "Tüm" in cleaned_cards and "Kart" in cleaned_cards:
                update_data['eligible_cards'] = "Tüm Kredi Kartları"
            else:
                update_data['eligible_cards'] = cleaned_cards
                
            fixed_cards_count += 1
            needs_update = True
            print(f"   🔧 Fixed cards for ID {row.id}: {update_data['eligible_cards']}")
            
        # Check conditions
        if row.conditions and is_corrupted(row.conditions[:100]):
            update_data['conditions'] = "Detaylar kampanya sayfasındadır."
            fixed_conditions_count += 1
            needs_update = True
            print(f"   🧹 Cleared conditions for ID {row.id} (too corrupted)")
            
        # Check Kuveytturk wrong images
        if row.image_url and "kuveytturk" in row.image_url.lower():
            if "logo" in row.image_url.lower() or "default" in row.image_url.lower() or "bireysel.png" in row.image_url.lower():
                update_data['image_url'] = None
                deleted_kuveytturk_imgs_count += 1
                needs_update = True
                print(f"   🖼️ Removed default image for Kuveytturk ID {row.id}")
                
        if needs_update:
            stmt = campaigns_table.update().where(campaigns_table.c.id == row.id).values(**update_data)
            conn.execute(stmt)
            
    conn.commit()

print(f"✅ Bitti. Düzeltilen kart verisi: {fixed_cards_count}, temizlenen koşul: {fixed_conditions_count}, Silinen Kuveyt resimleri: {deleted_kuveytturk_imgs_count}")
