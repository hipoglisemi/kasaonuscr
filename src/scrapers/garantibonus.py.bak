"""
Modernized Garanti Bonus Scraper
Combines proven navigation logic from old scraper with AI-powered parsing
"""
import time
import random
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from datetime import datetime
from decimal import Decimal

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..database import get_db_session
from ..models import Bank, Card, Sector, Brand, Campaign, CampaignBrand
from ..services.ai_parser import parse_api_campaign

class GarantiBonusScraper:
    """
    Garanti Bonus campaign scraper
    
    Uses proven CSS selectors and navigation from old scraper,
    but replaces complex regex parsing with AI
    """
    
    # Configuration (from old scraper)
    BASE_URL = "https://www.bonus.com.tr"
    CAMPAIGN_LIST_URL = "https://www.bonus.com.tr/kampanyalar"
    BANK_NAME = "Garanti BBVA"
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'no-cache',
    }
    
    def __init__(self, max_campaigns: int = 999):
        """
        Initialize scraper
        
        Args:
            max_campaigns: Maximum number of campaigns to scrape
        """
        self.max_campaigns = max_campaigns
        self.session = requests.Session()
        self.db: Optional[Session] = None
        
        # Cache for database lookups
        self.bank_cache: Optional[Bank] = None
        self.card_cache: Dict[str, Card] = {}
        self.sector_cache: Dict[str, Sector] = {}
        self.brand_cache: Dict[str, Brand] = {}
    
    def run(self):
        """Main execution flow"""
        print(f"🚀 Garanti Bonus Scraper - Modern AI Edition")
        print(f"=" * 60)
        
        try:
            # Get database session
            self.db = get_db_session()
            
            # Load cache
            self._load_cache()
            
            # Get campaign URLs (using old proven logic)
            campaign_urls = self._get_campaign_urls()
            print(f"✅ Found {len(campaign_urls)} campaign URLs")
            
            # Limit campaigns
            if len(campaign_urls) > self.max_campaigns:
                campaign_urls = campaign_urls[:self.max_campaigns]
            
            # Scrape each campaign
            success_count = 0
            for i, url in enumerate(campaign_urls, 1):
                print(f"\n[{i}/{len(campaign_urls)}] Processing: {url}")
                
                try:
                    if self._scrape_campaign(url):
                        success_count += 1
                    
                    # Rate limiting
                    time.sleep(random.uniform(0.5, 1.5))
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    continue
            
            print(f"\n{'=' * 60}")
            print(f"✅ Scraping complete!")
            print(f"   Total: {len(campaign_urls)} campaigns")
            print(f"   Success: {success_count}")
            print(f"   Failed: {len(campaign_urls) - success_count}")
            
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            raise
        
        finally:
            if self.db:
                self.db.close()
    
    def _load_cache(self):
        """Load database entities into cache"""
        print("Loading database cache...")
        
        # Load bank
        self.bank_cache = self.db.query(Bank).filter(Bank.name == self.BANK_NAME).first()
        if not self.bank_cache:
            print(f"   ⚠️  Bank '{self.BANK_NAME}' not found in database!")
            print(f"   Creating bank...")
            self.bank_cache = Bank(
                name=self.BANK_NAME,
                slug="garanti-bbva",
                is_active=True
            )
            self.db.add(self.bank_cache)
            self.db.commit()
        
        # Load cards
        cards = self.db.query(Card).filter(Card.bank_id == self.bank_cache.id).all()
        for card in cards:
            self.card_cache[card.name.lower()] = card
        
        # Load sectors
        sectors = self.db.query(Sector).all()
        for sector in sectors:
            self.sector_cache[sector.name.lower()] = sector
        
        # Load brands
        brands = self.db.query(Brand).all()
        for brand in brands:
            self.brand_cache[brand.name.lower()] = brand
        
        print(f"   ✅ Loaded: {len(self.card_cache)} cards, {len(self.sector_cache)} sectors, {len(self.brand_cache)} brands")
    
    def _get_campaign_urls(self) -> List[str]:
        """
        Get list of campaign URLs
        Uses proven logic from old scraper (lines 381-395)
        """
        print("Fetching campaign list...")
        urls = []
        
        try:
            resp = self.session.get(self.CAMPAIGN_LIST_URL, headers=self.HEADERS, timeout=20)
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Find all campaign links (old proven selector)
            for a in soup.find_all('a', href=True):
                href = a['href']
                
                # Filter campaign URLs (old proven logic)
                if '/kampanyalar/' in href and len(href.split('/')) > 2:
                    # Exclude non-campaign pages
                    if not any(x in href for x in ['sektor', 'kategori', 'marka', '#', 'javascript']):
                        full_url = urljoin(self.BASE_URL, href)
                        if full_url not in urls:
                            urls.append(full_url)
            
        except Exception as e:
            print(f"   ❌ Error fetching campaign list: {e}")
        
        return urls
    
    def _scrape_campaign(self, url: str) -> bool:
        """
        Scrape single campaign page
        
        Args:
            url: Campaign URL
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Fetch page
            resp = self.session.get(url, headers=self.HEADERS, timeout=15)
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Extract data using proven CSS selectors (from old scraper)
            title_elm = soup.select_one('.campaign-detail-title h1')
            title = title_elm.get_text().strip() if title_elm else "Başlık Bulunamadı"
            
            img_elm = soup.select_one('.campaign-detail__image img')
            image_url = urljoin(self.BASE_URL, img_elm['src']) if img_elm else None
            
            date_elm = soup.select_one('.campaign-date')
            date_text = date_elm.get_text().strip() if date_elm else ""
            
            # Get full text for AI parsing
            full_text = soup.get_text(separator=' ')
            
            print(f"   📄 Title: {title[:50]}...")

            # Duplicate Check using SQLAlchemy
            existing = self.db.query(Campaign).filter(Campaign.tracking_url == url).first()
            if existing:
                print(f"   ⏭️ Skipped (Already exists, preserving manual edits): {title[:50]}...")
                return True
            
            # 🧠 AI PARSER
            parsed_data = parse_api_campaign(
                title=title,
                short_description=title,
                content_html=full_text,
                bank_name=self.BANK_NAME,
                scraper_sector=None
            )
            
            # Get or create card
            card = self._get_or_create_card(parsed_data.get("cards", []))
            if not card:
                print(f"   ⚠️  No valid card found, using default")
                card = self._get_default_card()
            
            # Get sector
            sector = self._get_sector(parsed_data.get("sector"))
            
            # Get or create brands
            brand_ids = self._get_or_create_brands(
                parsed_data.get("brands", []),
                sector.id if sector else None
            )
            
            # Create campaign
            campaign = Campaign(
                card_id=card.id,
                sector_id=sector.id if sector else None,
                slug=parsed_data.get("slug") or title.lower().replace(" ", "-"),
                title=parsed_data.get("short_title") or title,
                reward_text=parsed_data.get("reward_text"),
                reward_value=Decimal(str(parsed_data["reward_value"])) if parsed_data.get("reward_value") else None,
                reward_type=parsed_data.get("reward_type"),
                description=parsed_data.get("short_description") or "",
                conditions="\n".join(parsed_data.get("conditions", [])),
                image_url=image_url,
                start_date=datetime.strptime(parsed_data["start_date"], "%Y-%m-%d") if parsed_data.get("start_date") else None,
                end_date=datetime.strptime(parsed_data["end_date"], "%Y-%m-%d") if parsed_data.get("end_date") else None,
                tracking_url=url,
                is_active=True
            )
            
            self.db.add(campaign)
            self.db.flush()  # Get campaign ID
            
            # Link brands
            for brand_id in brand_ids:
                campaign_brand = CampaignBrand(
                    campaign_id=campaign.id,
                    brand_id=brand_id
                )
                self.db.add(campaign_brand)
            
            self.db.commit()
            
            print(f"   ✅ Saved: {campaign.title[:40]}... (Reward: {campaign.reward_text})")
            return True
            
        except Exception as e:
            print(f"   ❌ Error scraping campaign: {e}")
            if self.db:
                self.db.rollback()
            return False
    
    def _get_or_create_card(self, card_names: List[str]) -> Optional[Card]:
        """Get or create card from list of names"""
        if not card_names:
            return None
        
        # Try to find existing card
        for name in card_names:
            name_lower = name.lower()
            if name_lower in self.card_cache:
                return self.card_cache[name_lower]
        
        # Create first card if not found
        first_card_name = card_names[0]
        card = Card(
            bank_id=self.bank_cache.id,
            name=first_card_name,
            slug=first_card_name.lower().replace(" ", "-"),
            is_active=True
        )
        self.db.add(card)
        self.db.flush()
        
        # Add to cache
        self.card_cache[first_card_name.lower()] = card
        
        print(f"   ➕ Created new card: {first_card_name}")
        return card
    
    def _get_default_card(self) -> Card:
        """Get or create default 'Garanti Bonus' card"""
        default_name = "Garanti Bonus"
        
        if default_name.lower() in self.card_cache:
            return self.card_cache[default_name.lower()]
        
        card = Card(
            bank_id=self.bank_cache.id,
            name=default_name,
            slug="garanti-bonus",
            is_active=True
        )
        self.db.add(card)
        self.db.flush()
        
        self.card_cache[default_name.lower()] = card
        return card
    
    def _get_sector(self, sector_name: Optional[str]) -> Optional[Sector]:
        """Get sector by name"""
        if not sector_name:
            return None
        
        sector_lower = sector_name.lower()
        return self.sector_cache.get(sector_lower)
    
    def _get_or_create_brands(
        self,
        brand_names: List[str],
        sector_id: Optional[int]
    ) -> List[str]:
        """Get or create brands and return their IDs"""
        brand_ids = []
        
        for name in brand_names:
            name_lower = name.lower()
            
            # Check cache
            if name_lower in self.brand_cache:
                brand_ids.append(str(self.brand_cache[name_lower].id))
                continue
            
            # Create new brand
            try:
                with self.db.begin_nested():
                    brand = Brand(
                        name=name,
                        sector_id=sector_id or 1,  # Default to first sector if none
                        aliases=[],
                        is_active=True
                    )
                    self.db.add(brand)
                    self.db.flush()
            except IntegrityError:
                brand = self.db.query(Brand).filter(Brand.name == name).first()
            
            if brand:
                # Add to cache
                self.brand_cache[name_lower] = brand
                brand_ids.append(str(brand.id))
                print(f"   ➕ Created/Fetched brand: {name}")
        
        return brand_ids


def main():
    """Run Garanti Bonus scraper"""
    scraper = GarantiBonusScraper()
    scraper.run()


if __name__ == "__main__":
    main()
