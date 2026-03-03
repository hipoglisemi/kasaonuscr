import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.database import get_db_session
from sqlalchemy import text

db = get_db_session()
try:
    res = db.execute(text("""
SELECT
    source_table.relname AS source_table,
    target_table.relname AS target_table
FROM
    pg_constraint
JOIN pg_class source_table ON pg_constraint.conrelid = source_table.oid
JOIN pg_class target_table ON pg_constraint.confrelid = target_table.oid
WHERE
    target_table.relname = 'test_campaigns' OR source_table.relname = 'test_campaigns';
    """))
    print("Dependencies involving test_campaigns:")
    for row in res:
        print(f"{row[0]} -> {row[1]}")
finally:
    db.close()
