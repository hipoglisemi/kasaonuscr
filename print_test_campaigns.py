import os
os.environ["TEST_MODE"] = "1"
from src.database import get_db_session
from src.models import Campaign
import json

db = get_db_session()
campaigns = db.query(Campaign).all()
for c in campaigns:
    print(f"--- \nTITLE: {c.title}")
    print(f"REWARD TEXT: {c.reward_text}")
    print(f"SECTOR: {c.sector.name if c.sector else 'None'}")
    print(f"DATES: {c.start_date} to {c.end_date}")
    print(f"CARDS: {c.eligible_cards}")
    print(f"PARTICIPATION: {c.category}")
    print(f"CONDITIONS:\n{c.conditions}")
