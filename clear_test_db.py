from src.database import get_db_session
from src.models import Campaign
import os

os.environ["TEST_MODE"] = "1"
db = get_db_session()
db.query(Campaign).delete()
db.commit()
print("Cleared test_campaigns table.")
