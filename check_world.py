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
cards_table = Table('cards', metadata, autoload_with=engine)

print("🔍 World kampanyaları inceleniyor...")

with engine.connect() as conn:
    # Get World card ID
    q_card = cards_table.select().where(cards_table.c.slug.like('%world%'))
    world_cards = conn.execute(q_card).fetchall()
    print("World kartları:", world_cards)
    
    if world_cards:
        world_card_id = world_cards[0].id
        
        # Get campaigns
        q = campaigns_table.select().where(campaigns_table.c.card_id == world_card_id).limit(10)
        campaigns = conn.execute(q).fetchall()
        
        for c in campaigns:
            print(f"ID: {c.id}")
            print(f"TITLE: {c.title}")
            print(f"CARDS: {c.eligible_cards}")
            print(f"IMAGE: {c.image_url}")
            print(f"CONDS: {str(c.conditions)[:50]}...")
            print("-" * 30)
