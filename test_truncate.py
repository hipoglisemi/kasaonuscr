import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.database import get_db_session
from sqlalchemy import text

db = get_db_session()
try:
    print("Executing truncate with cascade to see notices...")
    db.execute(text("TRUNCATE TABLE test_campaigns CASCADE;"))
finally:
    db.close()
