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

with engine.connect() as conn:
    result = conn.execute(campaigns_table.select().limit(50))
    for row in result:
        # Check if conditions has weird newlines or eligible_cards has weird format
        cards = row.eligible_cards or ""
        conds = row.conditions or ""
        
        if len(cards) > 25 and " " not in cards:
            print(f"--- CARD FOUND --- ID: {row.id}")
            print(f"CARDS REP: {repr(cards)}")
            
        if "\n" in conds:
            lines = conds.split('\n')
            short_lines = [l for l in lines if len(l.strip()) == 1]
            if len(short_lines) > 5:
                print(f"--- CONDS FOUND --- ID: {row.id}")
                print(f"CONDS REP: {repr(conds[:200])}")
