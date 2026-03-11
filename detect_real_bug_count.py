import os
from sqlalchemy import create_engine, MetaData, Table, text
from dotenv import load_dotenv

load_dotenv('.env')
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def detect_corrupted_patterns():
    with engine.connect() as conn:
        # Pattern 1: Virgüllü bozuk metinler (H, a, t, a gibi)
        # Pattern 2: Liste yerine string olarak kaydedilmiş ve bozulmuş veriler
        q = text("""
            SELECT count(*) 
            FROM campaigns 
            WHERE (
                conditions LIKE '%, %, %' OR 
                eligible_cards LIKE '%, %, %' OR
                description LIKE '%, %, %'
            )
        """)
        count = conn.execute(q).scalar()
        print(f"🔍 Found {count} campaigns with 'comma-separated character' pattern.")
        
        # Pattern 3: auto_corrected=True olup hala bozuk olanlar (eskiden düzelmiş sanılanlar)
        q2 = text("SELECT count(*) FROM campaigns WHERE auto_corrected = True")
        corrected_count = conn.execute(q2).scalar()
        print(f"📊 Total campaigns marked as 'auto_corrected': {corrected_count}")

if __name__ == "__main__":
    detect_corrupted_patterns()
