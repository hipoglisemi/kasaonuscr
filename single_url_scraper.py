#!/usr/bin/env python3
"""
Single URL Scraper - The Manual Trigger 🚀
Scrapes a single campaign URL from any bank and saves it to the database.
Uses Gemini AI for intelligent extraction.
"""

import os
import sys
import argparse
import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Add project root to path
sys.path.insert(0, str(os.path.abspath(os.path.dirname(__file__))))

from src.database import get_db_session
from src.models import Campaign, Bank, Card, Sector, Brand, CampaignBrand
from src.services.ai_parser import AIParser
from src.utils.slug_generator import get_unique_slug

def detect_bank_name(url: str) -> str:
    """Detect bank name from URL for AI hint"""
    url_lower = url.lower()
    if 'akbank' in url_lower or 'axess' in url_lower or 'wings' in url_lower:
        return "Akbank"
    if 'bonus' in url_lower or 'garanti' in url_lower or 'milesandsmiles' in url_lower or 'shopandfly' in url_lower:
        return "Garanti BBVA"
    if 'maximum' in url_lower or 'isbank' in url_lower or 'maximiles' in url_lower:
        return "İşbankası"
    if 'world' in url_lower or 'yapikredi' in url_lower:
        return "Yapı Kredi"
    if 'paraf' in url_lower or 'halkbank' in url_lower:
        return "Halkbank"
    if 'vakifbank' in url_lower:
        return "VakıfBank"
    if 'ziraat' in url_lower or 'bankkart' in url_lower:
        return "Ziraat Bankası"
    if 'deniz' in url_lower:
        return "Denizbank"
    if 'qnb' in url_lower or 'finansbank' in url_lower:
        return "QNB"
    if 'teb.com.tr' in url_lower:
        return "TEB"
    if 'enpara' in url_lower:
        return "Enpara"
    if 'chippin' in url_lower:
        return "Chippin"
    if 'turkiyefinans' in url_lower:
        return "Türkiye Finans"
    return "Bilinmeyen Banka"

def scrape_url(url: str):
    print(f"🚀 Starting Single URL Scrape: {url}")
    
    bank_name = detect_bank_name(url)
    print(f"🔍 Detected Bank Hint: {bank_name}")
    
    # 1. Fetch HTML
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        print(f"❌ Failed to fetch URL: {e}")
        return

    # 2. Extract Text
    soup = BeautifulSoup(html, 'html.parser')
    
    # Try to find a good image
    image_url = ""
    og_image = soup.find("meta", property="og:image")
    if og_image:
        image_url = og_image.get("content", "")
    
    if not image_url or "logo" in image_url.lower():
        # Fallback to first big image
        imgs = soup.find_all('img', src=True)
        for img in imgs:
            src = img['src']
            if 'kampanya' in src.lower() or 'banner' in src.lower() or 'slider' in src.lower():
                if src.startswith('http'):
                    image_url = src
                else:
                    parsed_uri = urlparse(url)
                    image_url = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri) + (src if src.startswith('/') else '/' + src)
                break

    # Clean text for AI
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.extract()
    raw_text = soup.get_text(separator=' ', strip=True)
    clean_text = raw_text[:15000]

    # 3. AI Parse
    print(f"🧠 Parsing with Gemini AI ({bank_name})...")
    parser = AIParser()
    ai_data = parser.parse_campaign_data(
        raw_text=clean_text,
        title=soup.title.string if soup.title else "Kampanya",
        bank_name=bank_name
    )

    if not ai_data:
        print("❌ AI parsing failed.")
        return

    # 4. Save to Database
    with get_db_session() as db:
        try:
            # Get or create Bank
            bank = db.query(Bank).filter(Bank.name.ilike(f"%{bank_name}%")).first()
            if not bank:
                # If even bank isn't found, we'll use a generic one or create it
                bank = db.query(Bank).filter(Bank.slug == "denizbank").first() # Fallback
            
            # Get or create Card
            card_name = ai_data.get("cards", ["Kredi Kartı"])[0] if ai_data.get("cards") else f"{bank_name} Kart"
            card = db.query(Card).filter(Card.bank_id == bank.id, Card.name.ilike(f"%{card_name}%")).first()
            if not card:
                card = db.query(Card).filter(Card.bank_id == bank.id).first() # Use first card of bank if perfect match fails
            
            # Get Sector
            sector_name = ai_data.get("sector", "Diğer")
            sector = db.query(Sector).filter(Sector.name.ilike(f"%{sector_name}%")).first()
            if not sector:
                sector = db.query(Sector).filter(Sector.slug == "diger").first()

            # Existing check
            existing = db.query(Campaign).filter(Campaign.tracking_url == url).first()
            if existing:
                print(f"⏭️ Campaign already exists (ID: {existing.id}). Updating title/dates...")
                existing.title = ai_data.get("title") or existing.title
                existing.end_date = ai_data.get("end_date")
                db.commit()
                print("✅ Updated!")
                return

            slug = get_unique_slug(ai_data.get("title") or "kampanya", db, Campaign)
            
            # Create Campaign
            campaign = Campaign(
                title=ai_data.get("title"),
                description=ai_data.get("description"),
                slug=slug,
                image_url=image_url or ai_data.get("imageUrl"),
                tracking_url=url,
                reward_text=ai_data.get("reward_text"),
                reward_value=ai_data.get("reward_value"),
                reward_type=ai_data.get("reward_type"),
                start_date=ai_data.get("start_date"),
                end_date=ai_data.get("end_date"),
                conditions="\n".join(ai_data.get("conditions", [])),
                eligible_cards=", ".join(ai_data.get("cards", [])),
                participation=ai_data.get("participation"),
                bank_id=bank.id,
                card_id=card.id if card else None,
                sector_id=sector.id if sector else None,
                is_active=True
            )
            
            db.add(campaign)
            db.flush() # Get ID
            
            # Brands
            brand_names = ai_data.get("brands", [])
            for bn in brand_names:
                brand = db.query(Brand).filter(Brand.name.ilike(f"%{bn}%")).first()
                if not brand:
                    brand = Brand(name=bn, slug=bn.lower().replace(" ", "-"), is_active=True)
                    db.add(brand)
                    db.flush()
                
                cb = CampaignBrand(campaign_id=campaign.id, brand_id=brand.id)
                db.add(cb)
            
            db.commit()
            print(f"✅ Successfully saved campaign: {campaign.title}")
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            db.rollback()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape a single campaign URL')
    parser.add_argument('url', type=str, help='The URL to scrape')
    args = parser.parse_args()
    
    scrape_url(args.url)
