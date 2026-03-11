import os
from sqlalchemy import create_engine, MetaData, Table, text
from dotenv import load_dotenv

load_dotenv('.env')
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)
metadata = MetaData()
metadata.reflect(bind=engine)

table_name = 'test_campaigns' if os.environ.get('TEST_MODE') == '1' else 'campaigns'
campaigns_table = Table(table_name, metadata, autoload_with=engine)

def find_all_corrupted():
    with engine.connect() as conn:
        # Pattern 1: Virgülle ayrılmış tek harfler (örneğin "P, a, r, a, f" veya "T, E, B")
        # Pattern 2: Çok uzun tek kelimeye dönüşmüş yapışık metinler ("Parafkredikartısanalkartlar") -> BOZUK DEĞİL, fixlenmiş hali.
        # Pattern 3: Yeni satırlar arasına sıkışmış tek karakterler (A\n \n \n...)
        
        # Bozuk yapışık kart isimleri veya description'ı 'Detayları İnceleyin' olan ama conditions'ı eksik/bozuk olanlar
        q = text("""
            SELECT id, title, conditions
            FROM campaigns
            WHERE (
                (conditions IS NULL OR length(conditions) < 15) OR
                (conditions = '[]') OR
                (title = 'Başlıksız Kampanya') OR
                (reward_text = 'Detayları İnceleyin' AND length(conditions) < 20)
            )
        """)
        results = conn.execute(q).fetchall()
        
        print(f"Total campaigns that are potentially missing data / corrupted: {len(results)}")
        if len(results) > 0:
            for r in results[:5]:
                print(f"ID {r.id}: {r.conditions[:50]}...")

if __name__ == "__main__":
    find_all_corrupted()
