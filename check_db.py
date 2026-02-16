
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import get_db_session
from src.models import Campaign, Card

def check_campaigns():
    with get_db_session() as db:
        # Check Maximiles (ID 49)
        max_count = db.query(Campaign).filter(Campaign.card_id == 49).count()
        print(f"Maximiles Digitus (ID 49): {max_count} campaigns")
        
        # Check Maximum Genç (ID 48)
        genc_count = db.query(Campaign).filter(Campaign.card_id == 48).count()
        print(f"Maximum Genç (ID 48): {genc_count} campaigns")
        
        # List last 5 titles for each
        print("\nLast 5 Maximiles:")
        for c in db.query(Campaign).filter(Campaign.card_id == 49).order_by(Campaign.id.desc()).limit(5):
            print(f"- {c.title}")
            
        print("\nLast 5 Genç:")
        for c in db.query(Campaign).filter(Campaign.card_id == 48).order_by(Campaign.id.desc()).limit(5):
            print(f"- {c.title}")

if __name__ == "__main__":
    check_campaigns()
