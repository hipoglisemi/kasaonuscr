from src.database import get_db_session
from src.models import Campaign, Card
from datetime import datetime

session = get_db_session()
try:
    # Get recent campaigns (last 10)
    campaigns = session.query(Campaign).order_by(Campaign.created_at.desc()).limit(10).all()
    
    print(f"Found {len(campaigns)} recent campaigns:\n")
    
    for c in campaigns:
        print(f"🔹 TITLE: {c.title}")
        print(f"   REWARD: {c.reward_text} (Val: {c.reward_value} {c.reward_type})")
        print(f"   DATES: {c.start_date} -> {c.end_date}")
        print(f"   SECTOR: {c.sector.name if c.sector else 'None'}")
        if c.conditions_text:
            print(f"   CONDITIONS (First 2 lines):")
            print('\n'.join(c.conditions_text.split('\n')[:2]))
        print("-" * 50)

except Exception as e:
    print(f"Error: {e}")
finally:
    session.close()
