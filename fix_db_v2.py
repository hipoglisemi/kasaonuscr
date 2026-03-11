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

def is_corrupted_cards(text):
    if not text:
        return False
    # Önceki scriptin birleştirdiği "ParafParaflysanalkartlarekkartlar" gibi kelimeleri tespit et (çok uzun kelimeler ve boşluksuz)
    if not " " in text and len(text) > 20: 
        return True
    
    # Orjinal virgüllü harfler: P , a , r , a
    pattern_commas = r'(.)\s*,\s*(.)\s*,\s*(.)'
    return bool(re.search(pattern_commas, text))

def is_corrupted_conditions(text):
    if not text:
         return False
    
    # Yeni durum: Harf harf alt alta yazılmış "\nK\na\nm\np\na" veya "K\na\nm"
    lines = text.split('\n')
    # Eğer satırların geneli SADECE TEK HARF ise bu corrupted'dır.
    single_char_lines = [l.strip() for l in lines if len(l.strip()) == 1]
    
    if len(lines) > 5 and len(single_char_lines) > len(lines) / 2:
        return True
        
    pattern_commas = r'(.)\s*,\s*(.)\s*,\s*(.)'
    return bool(re.search(pattern_commas, text[:100]))

print("🔍 Veritabanında alt alta/birleşik harf hataları olan kampanyalar tamamen taranıyor...")

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
            # Kart bilgisini onarmaktan çok sıfırlamak daha güvenli; Scraper zaten düzeltilmiş halini yeniden çekecek
            # Ancak scraper her kampanyayı update moduyla tek tek dönmeyebileceği için basit kelimelere çevirelim
            if "paraf" in row.eligible_cards.lower():
                update_data['eligible_cards'] = "Paraf, Parafly"
            elif "maximum" in row.eligible_cards.lower():
                update_data['eligible_cards'] = "Maximum"
            elif "bankkart" in row.eligible_cards.lower():
                update_data['eligible_cards'] = "Bankkart"
            elif "world" in row.eligible_cards.lower():
                update_data['eligible_cards'] = "World"
            else:
                update_data['eligible_cards'] = "Tüm Kartlar"
                
            fixed_cards_count += 1
            needs_update = True
            print(f"   🔧 Fixed cards for ID {row.id}: {row.eligible_cards[:20]}... -> {update_data['eligible_cards']}")
            
        # 2. Clean Conditions (Harf harf alt alta olanlar)
        if row.conditions and is_corrupted_conditions(row.conditions):
            # Harf harf olan "\n"li verileri birleştirsek bile çok bozuk oluyor ("K a m p a n...")
            # En iyisi tamamen jenerik mesaja çekmek.
            update_data['conditions'] = "Kampanya detayları ve tüm koşullar için lütfen ilgili bankanın kampanya sayfasını ziyaret ediniz."
            fixed_conditions_count += 1
            needs_update = True
            print(f"   🧹 Cleared conditions for ID {row.id}")
            
        if needs_update:
            stmt = campaigns_table.update().where(campaigns_table.c.id == row.id).values(**update_data)
            conn.execute(stmt)
            
    conn.commit()

print(f"✅ Bitti. Düzeltilen kart verisi: {fixed_cards_count}, temizlenen koşul: {fixed_conditions_count}")
