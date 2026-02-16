
from src.database import get_db_session
from src.models import Campaign

def check_images():
    db = get_db_session()
    campaigns = db.query(Campaign).filter(Campaign.tracking_url.like('%mock-campaign%')).limit(5).all()
    
    print(f"Found {len(campaigns)} mock campaigns.")
    for c in campaigns:
        print(f"Title: {c.title}")
        print(f"Image URL: {c.image_url}")
        print("-" * 20)
    
    db.close()

if __name__ == "__main__":
    check_images()
