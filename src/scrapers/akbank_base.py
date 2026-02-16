
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import random
from typing import List, Dict, Optional
from datetime import datetime

from src.models import Campaign, CampaignBrand
from src.database import get_db_session
from src.utils.slug_generator import generate_slug
from src.services.ai_parser import parse_api_campaign
from src.services.brand_normalizer import normalize_brand_name
from sqlalchemy.exc import IntegrityError

class AkbankBaseScraper:
    """
    Base scraper for Akbank brands (Axess, Free, Wings, Ticari).
    Handles:
    - AJAX list fetching
    - HTML detail parsing
    - AI content extraction
    - Database saving
    """
    
    def __init__(self, 
                 card_name: str, 
                 base_url: str, 
                 list_url: str, 
                 referer_url: str,
                 list_params: Dict = None):
        self.card_name = card_name
        self.base_url = base_url
        self.list_url = list_url
        self.referer_url = referer_url
        self.list_params = list_params or {'checkBox': '[0]', 'searchWord': '""'}
        
        self.session = requests.Session()
        self.session.headers.update({
             'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
             'Accept': 'application/json, text/plain, */*',
             'Referer': self.referer_url
        })
        
        # Helper to find card_id
        with get_db_session() as db:
            from src.models import Card
            card = db.query(Card).filter(Card.name == self.card_name).first()
            if not card:
                raise ValueError(f"Card '{self.card_name}' not found in DB. Please run seed_sectors.py first.")
            self.card = card
            self.card_id = card.id

    def _fetch_campaign_list(self) -> List[str]:
        """Iterate through AJAX pages to get all campaign URLs"""
        print(f"📥 Fetching campaign list for {self.card_name}...")
        campaign_urls = []
        page = 1
        
        while True:
            params = self.list_params.copy()
            params['page'] = page
            
            try:
                print(f"   Scanning page {page}...")
                response = self.session.get(self.list_url, params=params, timeout=20)
                response.raise_for_status()
                
                if 'kampanyadetay' not in response.text:
                    print(f"   Page {page} empty. Stopping.")
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.select('.campaingBox a.dLink')
                
                if not links:
                    print(f"   No links found on page {page}. Stopping.")
                    break
                    
                new_found = False
                for link in links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        if full_url not in campaign_urls:
                            campaign_urls.append(full_url)
                            new_found = True
                            
                if not new_found:
                    print("   No new campaigns found. Stopping.")
                    break
                    
                page += 1
                time.sleep(random.uniform(0.5, 1.0))
                
            except Exception as e:
                print(f"❌ Error fetching page {page}: {e}")
                break
                
        print(f"✅ Found {len(campaign_urls)} campaigns for {self.card_name}")
        return campaign_urls

    def _process_campaign(self, url: str):
        """Process a single campaign URL"""
        print(f"🔍 Processing: {url}")
        try:
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # --- 1. Raw HTML Extraction ---
            title_elm = soup.select_one('h2.pageTitle')
            title = title_elm.get_text(strip=True) if title_elm else "Kampanya"
            
            img_elm = soup.select_one('.campaingDetailImage img')
            image_url = None
            if img_elm:
                src = img_elm.get('src')
                if src:
                    image_url = urljoin(self.base_url, src)
            
            detail_container = soup.select_one('.cmsContent.clearfix')
            details_text = ""
            if detail_container:
                # Remove scripts and styles
                for script in detail_container(["script", "style"]):
                    script.decompose()
                details_text = detail_container.get_text(separator="\n", strip=True)
            else:
                details_text = title
                
            # --- 2. AI Parsing ---
            ai_data = parse_api_campaign(
                title=title,
                short_description=title, # Axess doesn't have a separate short desc
                content_html=details_text,
                bank_name="Akbank",
                scraper_sector=None
            )
            
            # --- 3. Save to DB ---
            self._save_campaign(title, details_text, image_url, ai_data, url)
            
        except Exception as e:
            print(f"❌ Failed to process {url}: {e}")

    def _save_campaign(self, title, details_text, image_url, ai_data, source_url):
        with get_db_session() as db:
            from src.models import Sector
            from src.utils.slug_generator import get_unique_slug
            
            # Use specific title from AI if available, otherwise fallback
            final_title = ai_data.get('short_title') or ai_data.get('title') or title
            
            # Check for existing campaign by source_url + card_id first
            existing_url = db.query(Campaign).filter(
                Campaign.tracking_url == source_url,
                Campaign.card_id == self.card_id
            ).first()
            
            if existing_url:
                print(f"   ⏭️  Skipped (URL already exists): {source_url}")
                return

            # Ensure slug is unique using the utility
            slug = get_unique_slug(final_title, db, Campaign)
            
            if not slug or slug == "kampanya":
                # Ultimate fallback if title is too generic
                import uuid
                slug = f"kampanya-{str(uuid.uuid4())[:8]}"

            # Map sector from AI data
            sector_name = ai_data.get('sector', 'Diğer')
            sector = db.query(Sector).filter(Sector.name == sector_name).first()
            if not sector:
                sector = db.query(Sector).filter(Sector.slug == 'diger').first()

            # Dates
            start_date = None
            if ai_data.get('start_date'):
               try:
                   start_date = datetime.strptime(ai_data['start_date'], '%Y-%m-%d')
               except: pass
               
            if not start_date:
                start_date = datetime.now() # Fallback for active campaigns

            end_date = None
            if ai_data.get('end_date'):
                try:
                    end_date = datetime.strptime(ai_data['end_date'], '%Y-%m-%d')
                except: pass

            # Build conditions text with participation and eligible cards
            conditions_lines = []
            
            # Add participation info
            participation = ai_data.get('participation')
            if participation and participation != "Detayları İnceleyin":
                conditions_lines.append(f"KATILIM: {participation}")
            
            # --- USER REQUEST: DO NOT REPEAT ELIGIBLE CARDS IN CONDITIONS ---
            eligible_cards_list = ai_data.get('cards', [])
            # (Previously added GEÇERLİ KARTLAR here, now removed)
            
            # Add AI conditions
            if ai_data.get('conditions'):
                conditions_lines.extend(ai_data.get('conditions'))
            
            conditions_text = "\n".join(conditions_lines)
            eligible_cards_str = ", ".join(eligible_cards_list) if eligible_cards_list else None

            campaign = Campaign(
                card_id=self.card_id,
                sector_id=sector.id if sector else None,
                slug=slug,
                title=ai_data.get('short_title') or ai_data.get('title') or title,
                description=ai_data.get('description') or title,
                reward_text=ai_data.get('reward_text'),
                reward_value=ai_data.get('reward_value'),
                reward_type=ai_data.get('reward_type'),
                conditions=conditions_text,
                eligible_cards=eligible_cards_str,
                image_url=image_url,
                start_date=start_date,
                end_date=end_date,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                tracking_url=source_url
            )
            
            db.add(campaign)
            db.commit()
            
            # --- Brands ---
            # Using normalize_brand_name utility
            if ai_data.get('brands'):
                for brand_name in ai_data['brands']:
                    # normalization logic not imported here to keep it simple, 
                    # relying on AI data usually being good enough or using utility if needed
                    from src.models import Brand
                    
                    b_slug = generate_slug(brand_name)
                    brand = db.query(Brand).filter(Brand.slug == b_slug).first()
                    if not brand:
                        brand = Brand(name=brand_name, slug=b_slug, is_active=True)
                        db.add(brand)
                        db.commit()
                        
                    cb = CampaignBrand(campaign_id=campaign.id, brand_id=brand.id)
                    db.add(cb)
                db.commit()

            print(f"   ✅ Saved: {campaign.title}")

    def run(self):
        print(f"🚀 Starting {self.card_name} Scraper...")
        urls = self._fetch_campaign_list()
        for i, url in enumerate(urls):
            print(f"[{i+1}/{len(urls)}]", end=" ")
            self._process_campaign(url)
            time.sleep(1) # Polite delay
        print("🏁 Scraping finished.")
