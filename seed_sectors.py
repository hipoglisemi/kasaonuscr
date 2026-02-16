from src.database import get_db_session
from src.models import Sector, Bank, Card

SECTORS = [
    {"name": "Market", "slug": "market", "icon_name": "ShoppingCart"},
    {"name": "Giyim", "slug": "giyim", "icon_name": "Shirt"},
    {"name": "Elektronik", "slug": "elektronik", "icon_name": "Monitor"},
    {"name": "Akaryakıt", "slug": "akaryakit", "icon_name": "Fuel"},
    {"name": "Restoran", "slug": "restoran", "icon_name": "Utensils"},
    {"name": "E-Ticaret", "slug": "e-ticaret", "icon_name": "Globe"},
    {"name": "Seyahat", "slug": "seyahat", "icon_name": "Plane"},
    {"name": "Sağlık", "slug": "saglik", "icon_name": "Activity"},
    {"name": "Eğitim", "slug": "egitim", "icon_name": "Book"},
    {"name": "Diğer", "slug": "diger", "icon_name": "MoreHorizontal"},
]

BANKS = [
    {"name": "Akbank", "slug": "akbank", "cards": [
        {"name": "Axess", "slug": "axess"},
        {"name": "Axess Free", "slug": "axess-free"},
        {"name": "Axess Business", "slug": "axess-business"},
        {"name": "Wings", "slug": "wings"}
    ]},
    {"name": "Garanti BBVA", "slug": "garanti", "cards": [
        {"name": "Garanti Bonus", "slug": "garanti-bonus"},
        {"name": "Garanti Miles&Smiles", "slug": "garanti-milessmiles"},
        {"name": "Garanti Shop&Fly", "slug": "garanti-shopandfly"}
    ]},
    {"name": "İşbankası", "slug": "isbankasi", "cards": [
        {"name": "Maximum", "slug": "maximum"},
        {"name": "Maximum Genç", "slug": "maximum-genc"},
        {"name": "Maximiles", "slug": "maximiles"}
    ]}
]

def seed_data():
    session = get_db_session()
    try:
        # 1. Sectors
        print("🌱 Seeding sectors...")
        for s_data in SECTORS:
            existing = session.query(Sector).filter(Sector.slug == s_data["slug"]).first()
            if not existing:
                sector = Sector(**s_data)
                session.add(sector)
                print(f"   Created sector: {s_data['name']}")
        session.commit()

        # 2. Banks & Cards
        print("🌱 Seeding banks & cards...")
        for b_data in BANKS:
            bank = session.query(Bank).filter(Bank.slug == b_data["slug"]).first()
            if not bank:
                bank = Bank(name=b_data["name"], slug=b_data["slug"], is_active=True)
                session.add(bank)
                session.flush() # get ID
                print(f"   Created bank: {b_data['name']}")
            
            for c_data in b_data["cards"]:
                card = session.query(Card).filter(Card.slug == c_data["slug"]).first()
                if not card:
                    card = Card(name=c_data["name"], slug=c_data["slug"], bank_id=bank.id, is_active=True)
                    session.add(card)
                    print(f"   Created card: {c_data['name']}")
        session.commit()

        print("✅ Seeding completed.")
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    seed_data()
