import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.database import get_db_session
from sqlalchemy import text

db = get_db_session()
try:
    res = db.execute(text("SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC;"))
    for row in res:
        print(f"{row[0]}: {row[1]}")
finally:
    db.close()
