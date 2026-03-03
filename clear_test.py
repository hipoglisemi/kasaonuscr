from src.database import get_db_session
from sqlalchemy import text
db = get_db_session()
db.execute(text("TRUNCATE TABLE test_campaigns CASCADE;"))
db.commit()
print("Table test_campaigns truncated via raw SQL.")
db.close()
