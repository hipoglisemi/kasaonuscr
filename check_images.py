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
banks_table = Table('banks', metadata, autoload_with=engine)

print("🔍 Image analysis across all banks...")

with engine.connect() as conn:
    # Let's get 5 campaigns from TEB, 5 from YapıKredi, 5 from Vakifbank
    q_banks = banks_table.select()
    banks = conn.execute(q_banks).fetchall()
    print([b.name for b in banks])
    
    # Just grab anything with worldcard or teb in URL
    q_all = campaigns_table.select().where(
        campaigns_table.c.image_url.like('%teb.com.tr%') |
        campaigns_table.c.image_url.like('%worldcard.com.tr%') |
        campaigns_table.c.tracking_url.like('%teb%') |
        campaigns_table.c.tracking_url.like('%world%')
    ).limit(30)
    
    campaigns = conn.execute(q_all).fetchall()
    
    for c in campaigns:
        print(f"ID: {c.id} | CARD_ID: {c.card_id} | TITLE: {c.title[:30]}")
        print(f"TRK URL: {c.tracking_url}")
        print(f"IMG URL: {c.image_url}")
        print("-" * 50)
