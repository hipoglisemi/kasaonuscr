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

table_name = 'test_campaigns' if os.environ.get('TEST_MODE') == '1' else 'campaigns'
campaigns_table = Table(table_name, metadata, autoload_with=engine)

# Pattern to catch mostly single characters separated by spaces or newlines
def is_corrupted_conditions(text):
    if not text:
        return False
        
    lines = text.split('\n')
    
    # Are more than 50% of the lines just 1 or 2 characters long?
    short_lines = [l for l in lines if len(l.strip()) <= 2 and l.strip()]
    total_lines = len([l for l in lines if l.strip()])
    
    if total_lines > 5 and len(short_lines) > (total_lines / 2):
        return True
        
    return False

def is_corrupted_cards(text):
    if not text:
        return False
        
    # Is it exactly one word but crazy long and unreadable, like "ParafParaflysanalkartlarekkartlar"
    if " " not in text.strip() and len(text.strip()) > 30:
        return True
        
    return False

print("🔍 Tüm problemli veriler taranıyor (V3)...")

with engine.connect() as conn:
    result = conn.execute(campaigns_table.select())
    campaigns = result.fetchall()
    
    fixed_cards_count = 0
    fixed_conditions_count = 0
    
    for row in campaigns:
        needs_update = False
        update_data = {}
        
        # 1. Clean Cards
        if row.eligible_cards and is_corrupted_cards(row.eligible_cards):
            c = row.eligible_cards.lower()
            if "paraf" in c:
                update_data['eligible_cards'] = "Paraf, Parafly, Sanal Kartlar"
            elif "maximum" in c:
                update_data['eligible_cards'] = "Maximum, Maximiles"
            else:
                update_data['eligible_cards'] = "Tüm Kredi Kartları"
                
            fixed_cards_count += 1
            needs_update = True
            print(f"   🔧 Fixed cards for ID {row.id}: {row.eligible_cards[:20]}... -> {update_data['eligible_cards']}")
            
        # 2. Clean Conditions (Harf harf alt alta olanlar)
        if row.conditions and is_corrupted_conditions(row.conditions):
            update_data['conditions'] = "Kampanya detayları ve tüm koşullar için lütfen ilgili bankanın kampanya sayfasını ziyaret ediniz."
            fixed_conditions_count += 1
            needs_update = True
            print(f"   🧹 Cleared conditions for ID {row.id}")
            
        if needs_update:
            stmt = campaigns_table.update().where(campaigns_table.c.id == row.id).values(**update_data)
            conn.execute(stmt)
            
    conn.commit()

print(f"✅ Bitti. Düzeltilen kart verisi: {fixed_cards_count}, temizlenen koşul: {fixed_conditions_count}")
