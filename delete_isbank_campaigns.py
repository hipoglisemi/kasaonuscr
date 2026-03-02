import os
import sys

# Proje dizinini sys.path'e ekle
project_root = '/Users/hipoglisemi/Desktop/kartavantaj-scraper'
sys.path.insert(0, project_root)

# dotenv'i manuel olarak çek
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, '.env'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Campaign, Bank, Card

DATABASE_URL = os.environ.get('DATABASE_URL')
# Güvenlik amaçlı connection'u echo ile başlatalım
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

# Banka adını veya slug'ını içeren kartları buluyoruz
cards = db.query(Card).all()
isbank_cards_id = []
for c in cards:
    bank_slug = c.bank.slug.lower() if c.bank and c.bank.slug else ""
    bank_name = c.bank.name.lower() if c.bank and c.bank.name else ""
    if "isbankasi" in bank_slug or "i-sbankasi" in bank_slug or "işbankası" in bank_name or "is bankasi" in bank_name:
        isbank_cards_id.append(c.id)

print(f"Işbankası card_ids: {isbank_cards_id}")

if isbank_cards_id:
    campaigns = db.query(Campaign).filter(Campaign.card_id.in_(isbank_cards_id)).all()
    print(f"Hetzner DB'de mevcut İşbankası kampanyası sayısı: {len(campaigns)}")
    
    deleted_count = 0
    for c in campaigns:
        db.delete(c)
        deleted_count += 1
        
    db.commit()
    print(f"Başarıyla SİLİNEN kampanya sayısı: {deleted_count}")
else:
    print("Veritabanında İşbankası'na ait bir kart bulunamadı.")
