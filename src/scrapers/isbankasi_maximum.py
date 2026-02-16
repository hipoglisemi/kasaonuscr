"""
İşbankası Maximum Scraper

IMPORTANT: This scraper requires special setup due to Cloudflare protection.

LOCAL DEVELOPMENT:
1. Start Chrome in debug mode BEFORE running this scraper:
   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome_dev_test"

2. Then run the scraper - it will connect to the debug Chrome instance

GITHUB ACTIONS:
- Uses undetected_chromedriver in headless mode
- No manual Chrome startup required
"""

import os
import time
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.database import get_db_session
from src.models import Campaign, Card, Sector, Bank
from src.services.ai_parser import parse_api_campaign
from src.utils.slug_generator import generate_slug


class IsbankMaximumScraper:
    """İşbankası Maximum card campaign scraper"""
    
    BASE_URL = "https://www.maximum.com.tr"
    CAMPAIGNS_URL = "https://www.maximum.com.tr/kampanyalar"
    BANK_NAME = "İşbankası"
    CARD_NAME = "Maximum"
    
    def __init__(self):
        self.driver = None
        self.card_id = None
        self._init_card()
    
    def _init_card(self):
        """Get Maximum card ID from database"""
        with get_db_session() as db:
            card = db.query(Card).join(Bank).filter(
                Bank.name == self.BANK_NAME,
                Card.name == self.CARD_NAME
            ).first()
            
            if not card:
                raise ValueError(f"Card '{self.CARD_NAME}' from '{self.BANK_NAME}' not found in database. Run seed_sectors.py first.")
            
            self.card_id = card.id
            print(f"✅ Found card: {self.BANK_NAME} {self.CARD_NAME} (ID: {self.card_id})")
    
    def _get_driver(self):
        """
        Initialize Selenium driver.
        Strategy:
        1. GitHub Actions: Use undetected_chromedriver (headless)
        2. Local: Try connecting to debug Chrome (localhost:9222)
        3. Local Fallback: Launch new undetected_chromedriver instance
        """
        # 1. GitHub Actions / Headless Env
        if os.getenv('GITHUB_ACTIONS'):
            try:
                import undetected_chromedriver as uc
                options = uc.ChromeOptions()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                driver = uc.Chrome(options=options)
                print("✅ Connected to undetected_chromedriver (GitHub Actions mode)")
                return driver
            except ImportError:
                raise ImportError("undetected_chromedriver not installed")

        # 2. Local: Try connecting to debug Chrome
        # 1. Local: Prioritize Undetected Chromedriver (Best for scraping)
        try:
            print("🚀 Switched to Strategy 3 (Prioritized): Launching new Chrome instance...")
            import undetected_chromedriver as uc
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--start-maximized')
            
            try:
                # Attempt 1: Auto-detect
                driver = uc.Chrome(options=options)
            except Exception as e:
                print(f"⚠️ Default UC launch failed: {e}")
                print("🔄 Retrying with specific version (144)...")
                options_retry = uc.ChromeOptions()
                options_retry.add_argument('--no-sandbox')
                options_retry.add_argument('--disable-dev-shm-usage')
                options_retry.add_argument('--window-size=1920,1080')
                options_retry.add_argument('--start-maximized')
                driver = uc.Chrome(options=options_retry, version_main=144)
            
            print("✅ Launched new undetected_chromedriver instance successfully!")
            time.sleep(5)  # ⏳ Wait for browser to settle
            return driver
        except Exception as e:
            print(f"⚠️ UC Launch failed, trying debug fallback: {e}")

        # 2. Fallback: Connect to debug Chrome
        try:
            print("🔄 Attempting to connect to debug Chrome (localhost:9222)...")
            options = Options()
            options.debugger_address = 'localhost:9222'
            
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service
                driver_path = ChromeDriverManager().install()
                service = Service(executable_path=driver_path)
                driver = webdriver.Chrome(service=service, options=options)
            except:
                driver = webdriver.Chrome(options=options)
                
            print("✅ Connected to debug Chrome")
            return driver
        except Exception as e:
             print(f"⚠️ Could not connect to debug Chrome: {e}")

        # 3. Last Resort: Standard Selenium
        return self._get_standard_driver()


    def _fetch_campaign_urls(self, limit: Optional[int] = None) -> List[str]:
        """
        Fetch all campaign URLs from the listing page.
        Uses infinite scroll to load all campaigns.
        """
        print(f"📥 Fetching campaign list from {self.CAMPAIGNS_URL}...")
        
        self.driver.get(self.CAMPAIGNS_URL)
        time.sleep(3)
        
        # Infinite scroll: Click "Daha Fazla" button until no more campaigns
        # Optimization: If limit is small (<= 10), just take what's on the first page to avoid crashes
        if limit and limit <= 10:
            print("   ℹ️ Small limit detected, skipping infinite scroll.")
            time.sleep(10)
        else:
            scroll_count = 0
            try:
                while True:
                    # Check if we have enough items (approximate)
                    if limit:
                        # Count current items to see if we reached limit
                        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                        count = len([a for a in soup.find_all('a', href=True) if '/kampanyalar/' in a['href'] 
                                     and 'arsiv' not in a['href'] 
                                     and not a['href'].endswith('-kampanyalari')
                                     and 'tum-kampanyalar' not in a['href']])
                        if count >= limit:
                            print(f"   ✅ Reached limit ({count} >= {limit}), stopping scroll.")
                            break
                    
                    scroll_count += 1
                    load_more_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Daha Fazla')]")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", load_more_btn)
                    time.sleep(1.5)
                    self.driver.execute_script("arguments[0].click();", load_more_btn)
                    time.sleep(2.5)
                    print(f"   ⏬ Loaded more campaigns (Scroll {scroll_count})...")
                    
            except Exception as e:
                print(f"   ⚠️ Scroll loop ended/failed: {e}")
                # Continue with whatever we have found so far
        
        # Extract campaign URLs
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        except:
             print("   ⚠️ Could not get page source. Returning empty/partial list.")
             return []

        excluded_slugs = [
            'bireysel', 'ticari', 'diger-kampanyalar', 'vergi-odemeleri', 
            'movenpick-hotel-istanbul-marmara-sea', 'kampanyalar-arsivi',
            'ozel-bankacilik' 
        ]
        
        all_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Exclude archive, past campaigns, and category pages
            if '/kampanyalar/' in href and 'arsiv' not in href \
               and '#gecmis' not in href and 'gecmis' not in href \
               and not href.endswith('-kampanyalari') \
               and 'tum-kampanyalar' not in href \
               and not any(ex in href for ex in excluded_slugs) \
               and len(href) > 20:
                full_url = urljoin(self.BASE_URL, href)
                all_links.append(full_url)
        
        unique_urls = list(dict.fromkeys(all_links))
        
        if limit:
            unique_urls = unique_urls[:limit]
        
        print(f"✅ Found {len(unique_urls)} campaigns")
        return unique_urls
    
    def _extract_campaign_data(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract campaign data from detail page.
        Returns dict with title, image, dates, and raw text.
        """
        try:
            self.driver.get(url)
            
            # 🔥 CRITICAL: Scroll to trigger image loading
            self.driver.execute_script("window.scrollTo(0, 600);")
            time.sleep(0.5)
            
            # Wait for campaign description to load
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span[id$='CampaignDescription']"))
                )
            except:
                pass
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract title
            title_el = soup.select_one('h1.gradient-title-text') or soup.find('h1')
            title = self._clean_text(title_el.text) if title_el else "Başlık Yok"
            
            # 🚨 1. Check for expired campaign indicators (URL or Title)
            if "gecmis" in url or "#gecmis" in url:
                print(f"   🚫 Skipped (Past campaign URL): {title}")
                return None
                
            if "geçmiş" in title.lower() or "süresi doldu" in title.lower():
                print(f"   🚫 Skipped (Past campaign title): {title}")
                return None

            # 🚨 2. Improved Date Extraction
            # Try multiple selectors for dates
            date_text = ""
            date_candidates = [
                soup.select_one("span[id$='KampanyaTarihleri']"),
                soup.select_one(".campaign-date"),
                soup.find("span", string=re.compile(r"Tarih", re.I)),
                soup.find("div", class_="date")
            ]
            
            for candidate in date_candidates:
                if candidate:
                    date_text = self._clean_text(candidate.text)
                    if date_text:
                        break
            
            # Check expiration based on parsed date
            end_date_iso = self._parse_date(date_text, is_end=True)
            if end_date_iso:
                try:
                    end_date = datetime.strptime(end_date_iso, "%Y-%m-%d")
                    if end_date < datetime.now():
                        print(f"   🚫 Skipped (Expired by date: {end_date_iso})")
                        return None
                except:
                    pass

            # 🚨 3. Extract Participation Method
            participation_text = ""
            part_candidates = [
                soup.find("span", string=re.compile(r"Katılım Şekli", re.I)),
                soup.select_one("span[id$='KatilimSekli']"),
                soup.find("div", class_="participation")
            ]
            for candidate in part_candidates:
                if candidate:
                    # Sometimes the text is in the next sibling or parent
                    participation_text = self._clean_text(candidate.text)
                    if len(participation_text) < 5: # If just label, look at sibling
                        sibling = candidate.find_next_sibling()
                        if sibling:
                            participation_text = self._clean_text(sibling.text)
                    break

            # Extract description and conditions
            desc_el = soup.select_one("span[id$='CampaignDescription']")
            conditions = []
            full_text = ""
            
            if desc_el:
                # Convert <br> and <p> to newlines
                for br in desc_el.find_all("br"):
                    br.replace_with("\n")
                for p in desc_el.find_all("p"):
                    p.insert(0, "\n")
                
                raw_text = desc_el.get_text()
                conditions = [self._clean_text(line) for line in raw_text.split('\n') if len(self._clean_text(line)) > 15]
                full_text = " ".join(conditions)
            else:
                full_text = self._clean_text(soup.get_text())
                conditions = [t for t in full_text.split('\n') if len(t) > 20]
            
            # Append explicit participation text to full_text for AI
            if participation_text:
                full_text += f"\nKATILIM ŞEKLİ: {participation_text}"
            
            # 🔥 CRITICAL: Extract image with specific selector
            image_url = None
            img_el = soup.select_one("img[id$='CampaignImage']")
            if img_el and img_el.get('src'):
                image_url = urljoin(self.BASE_URL, img_el['src'])
            
            return {
                'title': title,
                'image_url': image_url,
                'date_text': date_text,
                'full_text': full_text,
                'conditions': conditions,
                'source_url': url,
                'participation': participation_text 
            }
            
        except Exception as e:
            print(f"   ⚠️ Error extracting {url}: {e}")
            return None
    
    def _parse_date(self, date_text: str, is_end: bool = False) -> Optional[str]:
        """Parse Turkish date format to YYYY-MM-DD"""
        if not date_text:
            return None
        
        text = date_text.replace('İ', 'i').lower()
        months = {
            'ocak': '01', 'şubat': '02', 'mart': '03', 'nisan': '04',
            'mayıs': '05', 'haziran': '06', 'temmuz': '07', 'ağustos': '08',
            'eylül': '09', 'ekim': '10', 'kasım': '11', 'aralık': '12'
        }
        
        try:
            # Format: "1 Ocak - 31 Aralık 2026"
            pattern = r'(\d{1,2})\s*([a-zğüşıöç]+)?\s*-\s*(\d{1,2})\s*([a-zğüşıöç]+)\s*(\d{4})'
            match = re.search(pattern, text)
            
            if match:
                day1, month1, day2, month2, year = match.groups()
                if not month1:
                    month1 = month2
                
                if is_end:
                    return f"{year}-{months.get(month2, '12')}-{str(day2).zfill(2)}"
                else:
                    return f"{year}-{months.get(month1, '01')}-{str(day1).zfill(2)}"
        except:
            pass
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        text = text.replace('\n', ' ').replace('\r', '')
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _process_campaign(self, url: str):
        """Process a single campaign: extract, parse with AI, save"""
        # ---------------------------------------------------------
        # ⚡ OPTIMIZATION: Check if URL already exists in DB
        # ---------------------------------------------------------
        try:
            with get_db_session() as db:
                from src.models import Campaign
                exists = db.query(Campaign).filter(
                    Campaign.tracking_url == url,
                    Campaign.card_id == self.card_id
                ).first()
                if exists:
                    print(f"   ⏭️  Skipped (Already exists): {url}")
                    return
        except Exception as e:
            print(f"   ⚠️ URL check failed: {e}")
            # Continue if check fails, better to re-process than miss
            pass
        # ---------------------------------------------------------
        
        print(f"🔍 Processing: {url}")
        
        # Extract raw data
        data = self._extract_campaign_data(url)
        if not data:
            print("   ⏭️  Skipped (expired or invalid)")
            return
        
        # Parse with AI
        ai_result = parse_api_campaign(
            title=data['title'],
            short_description=data['full_text'][:500],  # First 500 chars as description
            content_html=data['full_text'],
            bank_name=self.BANK_NAME
        )
        
        # Save to database
        self._save_campaign(
            title=data['title'],
            image_url=data['image_url'],
            date_text=data['date_text'],
            source_url=data['source_url'],
            ai_data=ai_result
        )
    
    def _save_campaign(self, title: str, image_url: Optional[str], date_text: str, source_url: str, ai_data: Dict[str, Any]):
        """Save campaign to database"""
        print(f"   💾 Saving campaign: {title[:30]}...")
        try:
            with get_db_session() as db:
                from src.scrapers.isbankasi_maximum import Campaign
                from src.models import Sector
                from src.utils.slug_generator import get_unique_slug
                
                # Check card ID validity
                if not self.card_id:
                    print("   ❌ Error: self.card_id is not set!")
                    return

                # Generate slug
                slug = get_unique_slug(ai_data.get('short_title') or title, db, Campaign)
                
                # Check if exists
                existing = db.query(Campaign).filter(
                    Campaign.slug == slug,
                    Campaign.card_id == self.card_id
                ).first()
                
                if existing:
                    print(f"   ⚠️ Campaign already exists: {slug}")
                    return
                
                # Map sector
                sector_name = ai_data.get('sector', 'Diğer')
                sector = db.query(Sector).filter(Sector.name == sector_name).first()
                if not sector:
                    sector = db.query(Sector).filter(Sector.slug == 'diger').first()
                
                # Parse dates
                start_date = None
                if ai_data.get('start_date'):
                    try:
                        start_date = datetime.strptime(ai_data['start_date'], '%Y-%m-%d')
                    except:
                        pass
                
                if not start_date:
                    # Fallback to parsing from date_text
                    start_date_str = self._parse_date(date_text, is_end=False)
                    if start_date_str:
                        try:
                            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                        except:
                            pass
                
                if not start_date:
                    start_date = datetime.now()
                
                end_date = None
                if ai_data.get('end_date'):
                    try:
                        end_date = datetime.strptime(ai_data['end_date'], '%Y-%m-%d')
                    except:
                        pass
                
                if not end_date:
                    # Fallback to parsing from date_text
                    end_date_str = self._parse_date(date_text, is_end=True)
                    if end_date_str:
                        try:
                            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                        except:
                            pass
                
                # Build conditions with participation and cards
                conditions_lines = []
                
                participation = ai_data.get('participation')
                if participation and participation != "Detayları İnceleyin":
                    conditions_lines.append(f"KATILIM: {participation}")
                
                # Eligible cards are already stored in 'eligible_cards' column
                # No need to duplicate them in conditions text per user request
                eligible_cards_list = ai_data.get('cards', [])
                
                if ai_data.get('conditions'):
                    conditions_lines.extend(ai_data.get('conditions'))
                
                conditions_text = "\n".join(conditions_lines)
                eligible_cards_str = ", ".join(eligible_cards_list) if eligible_cards_list else None
                
                # Create campaign
                campaign = Campaign(
                    card_id=self.card_id,
                    sector_id=sector.id if sector else None,
                    slug=slug,
                    title=ai_data.get('short_title') or title,
                    description=ai_data.get('description') or title[:200],
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
                print("   📝 Added to session...")
                
                # ---------------------------------------------------------
                # NEW: Save Brands
                # ---------------------------------------------------------
                if ai_data.get('brands'):
                    from src.models import Brand, CampaignBrand
                    
                    for brand_name in ai_data['brands']:
                        clean_name = brand_name.strip()
                        if not clean_name:
                            continue
                            
                        # Generate brand slug
                        brand_slug = generate_slug(clean_name)
                        
                        # Check if brand exists by slug
                        brand = db.query(Brand).filter(Brand.slug == brand_slug).first()
                        
                        # Fallback: Check by name to avoid unique constraint violation
                        if not brand:
                            brand = db.query(Brand).filter(Brand.name == clean_name).first()
                            
                        if not brand:
                            # Create new brand
                            brand = Brand(
                                name=clean_name,
                                slug=brand_slug,
                                is_active=True,
                                aliases=[clean_name] # Add name as alias initially
                            )
                            db.add(brand)
                            db.flush() # Flush to get ID if needed (though UUID is usually client-side generated or default)
                            print(f"      ✨ Created new brand: {clean_name}")
                        else:
                             print(f"      ✓ Brand exists: {clean_name}")
                        
                        # Link to campaign
                        # Check if link exists (paranoia check)
                        # Since we just created the campaign, it shouldn't exist, but safe is safe
                        # Actually we need campaign.id, so we must flush campaign first
                        db.flush() 
                        
                        # Check if link already exists
                        existing_link = db.query(CampaignBrand).filter(
                            CampaignBrand.campaign_id == campaign.id,
                            CampaignBrand.brand_id == brand.id
                        ).first()
                        
                        if not existing_link:
                            link = CampaignBrand(
                                campaign_id=campaign.id,
                                brand_id=brand.id
                            )
                            db.add(link)
                            print(f"      🔗 Linked brand: {clean_name}")
                # ---------------------------------------------------------

                db.commit()
                print(f"   ✅ Saved: {campaign.title} (ID: {campaign.id})")
        except Exception as e:
            print(f"   ❌ Save Failed: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self, limit: Optional[int] = None):
        """
        Main scraper entry point.
        
        Args:
            limit: Maximum number of campaigns to scrape (None = all)
        """
        try:
            print(f"🚀 Starting İşbankası Maximum Scraper...")
            
            # Initialize driver
            self.driver = self._get_driver()
            self.driver.set_page_load_timeout(60)
            
            # Fetch campaign URLs
            urls = self._fetch_campaign_urls(limit=limit)
            
            # Process each campaign
            for i, url in enumerate(urls, 1):
                print(f"\n[{i}/{len(urls)}]")
                self._process_campaign(url)
                time.sleep(1.5)  # Be nice to the server
            
            print(f"\n🏁 Scraping finished. Processed {len(urls)} campaigns.")
            
        except Exception as e:
            print(f"❌ Scraper error: {e}")
            raise
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass


if __name__ == "__main__":
    scraper = IsbankMaximumScraper()
    scraper.run(limit=5)  # Test with 5 campaigns
