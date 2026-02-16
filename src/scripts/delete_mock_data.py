
from src.database import get_db_session
from src.models import Campaign

def clean_mock_data():
    db = get_db_session()
    # Delete campaigns with mock URL
    deleted = db.query(Campaign).filter(Campaign.tracking_url.like('%mock-campaign%')).delete(synchronize_session=False)
    db.commit()
    db.close()
    print(f"🧹 Deleted {deleted} mock campaigns.")

if __name__ == "__main__":
    clean_mock_data()
