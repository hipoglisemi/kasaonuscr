import os
import sys
from collections import defaultdict
from src.database import get_db_session
from src.models import Campaign

def inspect_campaigns(ids):
    with get_db_session() as db:
        campaigns = db.query(Campaign).filter(Campaign.id.in_(ids)).all()
        for c in campaigns:
            print("-" * 50)
            print(f"ID: {c.id}")
            print(f"Title: {c.title}")
            print(f"Tracking URL: {repr(c.tracking_url)}")
            print(f"Image URL: {c.image_url}")
            print(f"Card ID: {c.card_id}")
            print(f"Is Active: {c.is_active}")
            print(f"Start Date: {c.start_date}")
            print(f"End Date: {c.end_date}")
            print(f"Created At: {c.created_at}")
            print(f"Updated At: {c.updated_at}")
            print("-" * 50)

def find_duplicates():
    with get_db_session() as db:
        all_campaigns = db.query(Campaign).filter(Campaign.is_active == True).all()
        
        # We can define a duplicate by same tracking_url or same (title, card_id)
        url_map = defaultdict(list)
        title_card_map = defaultdict(list)
        
        for c in all_campaigns:
            if c.tracking_url:
                url_map[c.tracking_url].append(c.id)
            if c.title and c.card_id:
                title_card_map[(c.title, c.card_id)].append(c.id)
        
        print("\n--- Duplicates by Tracking URL ---")
        for url, ids in url_map.items():
            if len(ids) > 1:
                print(f"URL: {url}")
                print(f"Campaign IDs: {ids}")
                
        print("\n--- Duplicates by Title & Card ID ---")
        for tb, ids in title_card_map.items():
            if len(ids) > 1:
                title, card_id = tb
                print(f"Card ID: {card_id} | Title: {title}")
                print(f"Campaign IDs: {ids}")

if __name__ == "__main__":
    print("Inspecting 1530 and 1984:")
    inspect_campaigns([1530, 1984])
    print("\nFinding other active duplicates...")
    find_duplicates()
