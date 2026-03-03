import os
os.environ["TEST_MODE"] = "1"
from src.database import get_db_session
from src.models import Campaign

db = get_db_session()
campaigns = db.query(Campaign).all()
print(f"Found {len(campaigns)} test campaigns in DB")
for c in campaigns:
    print(c.title, getattr(c, 'card_id', 'no-card'))
