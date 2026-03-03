import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.database import get_db_session
from src.models import Campaign

db = get_db_session()
try:
    print("Live Campaigns:", db.query(Campaign).count())
finally:
    db.close()
