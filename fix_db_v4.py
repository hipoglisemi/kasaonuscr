import os
from sqlalchemy import create_engine, MetaData, Table
from dotenv import load_dotenv

load_dotenv('.env')
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)
metadata = MetaData()
metadata.reflect(bind=engine)

table_name = 'test_campaigns' if os.environ.get('TEST_MODE') == '1' else 'campaigns'
campaigns_table = Table(table_name, metadata, autoload_with=engine)

print("🔍 Daha agresif temizleme scripti başlatılıyor...")

with engine.connect() as conn:
    result = conn.execute(campaigns_table.select())
    campaigns = result.fetchall()
    
    fixed_count = 0
    
    for row in campaigns:
        needs_update = False
        update_data = {}
        
        cards = row.eligible_cards or ""
        conds = row.conditions or ""
        
        # 1. Agresif Kart Temizliği
        # Eğer string çok uzunsa (mesela > 30 karakter) ve içinde "Tüm Kredi Kartları" filan yoksa,
        # Ya da kullanıcı görselinde gördüğümüz "ParafParaflysanalkartlarekkartlar" tarzı kelimelerse
        if len(cards) > 25 and "Kredi Kart" not in cards and "Maxi" not in cards and "Bankkart" not in cards and "World" not in cards:
            if "Paraf" in cards:
                update_data['eligible_cards'] = "Paraf, Parafly, Sanal Kartlar"
                needs_update = True
        elif "ParafParafly" in cards:
             update_data['eligible_cards'] = "Paraf, Parafly, Sanal Kartlar"
             needs_update = True
             
        # QNB veya TEB için "Tüm, kartlar" vb gibi hatalar var mıydı?
        if "," in cards and len(cards.split(',')) > 5:
             # Very likely character-split issue
             update_data['eligible_cards'] = "Kampanyaya Dahil Kartlar"
             needs_update = True

        # 2. Agresif Koşul Temizliği (Alt alta olanlar)
        # Sadece \n ile bölünmüş, her biri 1-3 karakter olan çok fazla satır varsa
        lines = conds.split('\n')
        short_lines = [l for l in lines if len(l.strip()) <= 3]
        if len(lines) > 5 and len(short_lines) > len(lines) * 0.4:
            update_data['conditions'] = "Kampanya detayları ve tüm koşullar için lütfen ilgili bankanın kampanya sayfasını ziyaret ediniz."
            needs_update = True

        if needs_update:
            stmt = campaigns_table.update().where(campaigns_table.c.id == row.id).values(**update_data)
            conn.execute(stmt)
            fixed_count += 1
            print(f"🔧 Sabitlenen ID: {row.id} | Yeni Kart: {update_data.get('eligible_cards')} | Koşul Silindi: {'conditions' in update_data}")
            
    conn.commit()

print(f"✅ Bitti. Toplam güncellenen kampanya sayısı: {fixed_count}")
