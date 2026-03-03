import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.database import get_db_session
from src.models import Campaign, TestCampaign
from sqlalchemy import text

db = get_db_session()
try:
    print("Initial main campaigns:", db.query(Campaign).count())
    print("Initial test campaigns:", db.query(TestCampaign).count())
    
    # Insert dummy main campaign
    c = Campaign(title="DUMMY_MAIN", slug="dummy-main", cardId=1)
    db.add(c)
    db.commit()
    
    print("After insert main campaigns:", db.query(Campaign).count())
    
    # Truncate test_campaigns
    db.execute(text("TRUNCATE TABLE test_campaigns CASCADE;"))
    db.commit()
    
    print("After truncate main campaigns:", db.query(Campaign).count())
    
    # Cleanup
    db.query(Campaign).filter_by(title="DUMMY_MAIN").delete()
    db.commit()
    print("Main campaigns restored:", db.query(Campaign).count())
finally:
    db.close()
