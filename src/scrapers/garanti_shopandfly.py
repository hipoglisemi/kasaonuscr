
import requests
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from sqlalchemy.orm import Session

from src.database import get_db_session
from src.models import Campaign, Bank, Card, Sector, Brand, CampaignBrand
from src.services.ai_parser import parse_api_campaign
from src.utils.slug_generator import get_unique_slug
from src.utils.cache_manager import clear_cache
from sqlalchemy.exc import IntegrityError

class GarantiShopAndFlyScraper:
    """Scraper for Garanti Shop&Fly campaigns (UIkit based)."""
    
    BASE_URL = 'https://www.shopandfly.com.tr'
    CAMPAIGN_LIST_URL = 'https://www.shopandfly.com.tr/kampanyalar'
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Cache-Control': 'no-cache',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.bank = None
        self.card = None
    
    def _get_or_create_bank(self):
        """Get or create Garanti BBVA bank"""
        with get_db_session() as db:
            bank = db.query(Bank).filter(Bank.name == "Garanti BBVA").first()
            if not bank:
                bank = Bank(
                    name="Garanti BBVA",
                    slug="garanti-bbva",
                    is_active=True
                )
                db.add(bank)
                db.commit()
                db.refresh(bank)
                print(f"✅ Created bank: Garanti BBVA")
            self.bank = bank
            return bank
    
    def _get_or_create_card(self):
        """Get or create Garanti Shop&Fly card"""
        with get_db_session() as db:
            card = db.query(Card).filter(
                Card.bank_id == self.bank.id,
                Card.name == "Garanti Shop&Fly"
            ).first()
            
            if not card:
                card = Card(
                    bank_id=self.bank.id,
                    name="Garanti Shop&Fly",
                    slug="garanti-shopandfly",
                    is_active=True
                )
                db.add(card)
                db.commit()
                db.refresh(card)
                print(f"✅ Created card: Garanti Shop&Fly")
            
            self.card = card
            return card
    
    def _fetch_campaign_list(self) -> List[str]:
        """Fetch all campaign URLs from the main listing page."""
        print(f"📥 Fetching campaign list from {self.CAMPAIGN_LIST_URL}")
        
        try:
            response = self.session.get(
                self.CAMPAIGN_LIST_URL,
                headers=self.HEADERS,
                timeout=20
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            campaign_links = []
            # Find all links starting with /kampanyalar/
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('/kampanyalar/') and len(href.split('/')) > 2:
                     # Filter out non-campaign lists if any
                    full_url = urljoin(self.BASE_URL, href)
                    if full_url not in campaign_links:
                        campaign_links.append(full_url)
            
            print(f"✅ Found {len(campaign_links)} campaigns")
            return campaign_links
            
        except Exception as e:
            print(f"❌ Error fetching campaign list: {e}")
            return []
    
    def _process_campaign(self, url: str) -> bool:
        """Process a single campaign page."""
        try:
            response = self.session.get(url, headers=self.HEADERS, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Title
            title_elm = soup.find('h1')
            title = title_elm.get_text().strip() if title_elm else "Başlık Bulunamadı"
            
            # Image - Try multiple selectors
            img_container = soup.select_one('.campaignDetail img, .campaign-detail img, .uk-width-expand img')
            image_url = None
            if img_container:
                image_url = img_container.get('src') or img_container.get('data-src')
                if image_url and not image_url.startswith('http'):
                    image_url = urljoin(self.BASE_URL, image_url)
            
            # Dates - Specific HTML Extraction (More reliable than AI for this site)
            start_date = None
            end_date = None
            
            # Find the header "Başlangıç - Bitiş Tarihleri" (h2, h3, p, strong, etc.)
            date_header = soup.find(lambda tag: tag.name in ['h2', 'h3', 'h4', 'h5', 'strong', 'b', 'p'] and 
                                   'Başlangıç - Bitiş Tarihleri' in tag.get_text())
            
            if date_header:
                # The date usually follows immediately after, either as next sibling or in the next block
                # Try next sibling text first
                date_text = ""
                next_elem = date_header.find_next_sibling()
                if next_elem:
                    date_text = next_elem.get_text().strip()
                
                # If not found, look at the parent's text or next element in hierarchy
                if not date_text:
                    parent = date_header.parent
                    if parent:
                        # Extract text from parent, removing the header text
                        full_text = parent.get_text().strip()
                        header_text = date_header.get_text().strip()
                        date_text = full_text.replace(header_text, '').strip()

                # Parse simple date range: "01.02.2026 - 28.02.2026"
                import re
                date_pattern = r'(\d{1,2}\.\d{1,2}\.\d{4})\s*-\s*(\d{1,2}\.\d{1,2}\.\d{4})'
                match = re.search(date_pattern, date_text)
                if match:
                    try:
                        start_date = datetime.strptime(match.group(1), "%d.%m.%Y")
                        end_date = datetime.strptime(match.group(2), "%d.%m.%Y")
                        print(f"   📅 Found Dates: {start_date.date()} - {end_date.date()}")
                    except:
                        pass

            # Content for AI
            main_content = ""
            # Convert soup to text preserving newlines
            main_content = soup.get_text(separator='\n') 
            
            print(f"   📄 {title[:60]}...")
            
            # AI Parsing
            ai_data = parse_api_campaign(
                title=title,
                short_description=title, # Let AI generate better one
                content_html=main_content, # Sending full text works well for Gemini
                bank_name="Garanti BBVA",
                scraper_sector=None
            )
            
            # Dates Fallback (Use AI data only if HTML extraction failed)
            if not start_date and ai_data.get('start_date'):
                try:
                    start_date = datetime.strptime(ai_data['start_date'], "%Y-%m-%d")
                except:
                    pass
            
            if not end_date and ai_data.get('end_date'):
                try:
                    end_date = datetime.strptime(ai_data['end_date'], "%Y-%m-%d")
                except:
                    pass

            # Update start_date logic (user request: default to today if missing)
            if not start_date and end_date:
                try:
                    start_today = datetime.utcnow().date()
                    if start_today <= end_date.date():
                        start_date = datetime(start_today.year, start_today.month, start_today.day)
                    else:
                        start_date = end_date
                except:
                    pass
            
            # Save campaign
            self._save_campaign(
                title=title,
                details_text=ai_data.get('short_description'),
                image_url=image_url,
                tracking_url=url,
                start_date=start_date,
                end_date=end_date,
                ai_data=ai_data
            )
            
            return True
            
        except Exception as e:
             print(f"   ❌ Error processing campaign: {e}")
             return False

    def _save_campaign(self, title: str, details_text: str, image_url: Optional[str],
                       tracking_url: str, start_date, end_date, ai_data: Dict[str, Any]):
        """Save campaign to database"""
        with get_db_session() as db:
            # Check if campaign already exists
            existing = db.query(Campaign).filter(Campaign.tracking_url == tracking_url).first()
            if existing:
                print(f"   ⏭️ Skipped (Already exists, preserving manual edits): {title[:50]}...")
                return

            slug = get_unique_slug(title, db, Campaign)
            
            # Sector
            sector_id = None
            if ai_data.get('sector'):
                sector = db.query(Sector).filter(Sector.name == ai_data['sector']).first()
                if sector:
                    sector_id = sector.id
            
            # Conditions
            conditions_list = ai_data.get('conditions', [])
            conditions_text = '\n'.join(conditions_list)
            
            participation = ai_data.get('participation')
            if participation and participation != "Otomatik katılım":
                conditions_text = f"KATILIM: {participation}\n\n" + conditions_text
            
            # Eligible Cards
            eligible_cards_str = None
            cards_list = ai_data.get('cards', [])
            if cards_list:
                eligible_cards_str = ', '.join(cards_list)
                if len(eligible_cards_str) > 255:
                    eligible_cards_str = eligible_cards_str[:255]
            
            # Create campaign
            campaign = Campaign(
                card_id=self.card.id,
                sector_id=sector_id,
                slug=slug,
                title=ai_data.get('short_title') or ai_data.get('title') or title,
                reward_text=ai_data.get('reward_text'),
                reward_value=ai_data.get('reward_value'),
                reward_type=ai_data.get('reward_type'),
                description=details_text,
                conditions=conditions_text,
                eligible_cards=eligible_cards_str,
                image_url=image_url,
                start_date=start_date,
                end_date=end_date,
                tracking_url=tracking_url,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(campaign)
            db.flush()
            
            # Brands
            brand_names = ai_data.get('brands', [])
            if brand_names:
                for brand_name in brand_names:
                    brand = db.query(Brand).filter(Brand.name == brand_name).first()
                    if not brand:
                        try:
                            with db.begin_nested():
                                brand = Brand(name=brand_name, slug=brand_name.lower().replace(' ', '-'), is_active=True)
                                db.add(brand)
                                db.flush()
                        except IntegrityError:
                            brand = db.query(Brand).filter(Brand.name == brand_name).first()
                    
                    if brand:
                        campaign_brand = CampaignBrand(campaign_id=campaign.id, brand_id=brand.id)
                        db.add(campaign_brand)
            
            db.commit()
            print(f"   ✅ Saved: {campaign.title[:50]}... (Reward: {campaign.reward_text})")

    def run(self):
        """Main execution flow"""
        print("🚀 Garanti Shop&Fly Scraper - UIkit Edition")
        print("=" * 60)
        
        try:
            # Setup
            self._get_or_create_bank()
            self._get_or_create_card()
            
            # Fetch campaign list
            campaign_urls = self._fetch_campaign_list()
            
            if not campaign_urls:
                print("❌ No campaigns found!")
                return
            
            # Process campaigns
            success_count = 0
            for i, url in enumerate(campaign_urls, 1):
                print(f"\n[{i}/{len(campaign_urls)}] Processing: {url}")
                
                if self._process_campaign(url):
                    success_count += 1
                
                # Rate limiting
                time.sleep(0.8)
            
            print(f"\n{'=' * 60}")
            print(f"✅ Scraping complete!")
            print(f"   Total: {len(campaign_urls)} campaigns")
            print(f"   Success: {success_count}")
            print(f"   Failed: {len(campaign_urls) - success_count}")
            
            # Clear cache
            clear_cache()
            
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            raise

if __name__ == "__main__":
    scraper = GarantiShopAndFlyScraper()
    scraper.run()
