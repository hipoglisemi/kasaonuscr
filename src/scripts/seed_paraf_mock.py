
import asyncio
import random
from datetime import datetime, timedelta
from ..scrapers.paraf import ParafScraper

async def seed_mock_data():
    print("🌱 Seeding 10 Mock Paraf Campaigns...")
    scraper = ParafScraper(max_campaigns=10)
    # Use the module level function
    from ..database import get_db_session
    scraper.db = get_db_session()
    
    scraper._load_cache()
    
    sectors = ["Market", "Giyim", "Restoran", "Akaryakıt", "Elektronik"]
    
    for i in range(1, 11):
        sector_name = random.choice(sectors)
        reward_amt = random.choice([50, 100, 200, 500])
        
        mock_data = {
            "title": f"Paraf ile {sector_name} Alışverişinize {reward_amt} TL ParafPara",
            "description": f"{sector_name} sektöründe yapacağınız 1000 TL ve üzeri harcamaya {reward_amt} TL ParafPara hediye! Kampanya detayları için tıklayın.",
            "reward_value": reward_amt,
            "reward_type": "points",
            "reward_text": f"{reward_amt} TL ParafPara",
            "min_spend": 1000,
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "sector": sector_name,
            "brands": [],
            "cards": ["Paraf", "Parafly"],
            "conditions": ["Kampanya katılımı zorunludur.", "Sadece POS cihazlarında geçerlidir."]
        }
        
        fake_url = f"https://www.paraf.com.tr/mock-campaign-{i}"
        fake_image = f"https://placehold.co/600x400/00a0dc/ffffff?text={sector_name}+Kampanya"
        print(f"   Simulating: {mock_data['title']}")
        scraper._save_campaign(mock_data, fake_url, fake_image)
        
    print("✅ Seed complete.")

if __name__ == "__main__":
    asyncio.run(seed_mock_data())
