"""
İşbankası Maximiles Scraper
"""

import os
import time
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import sys

# Virtual Display (for GitHub Actions / Headless)
try:
    from pyvirtualdisplay import Display
    HAS_VIRTUAL_DISPLAY = True
except ImportError:
    HAS_VIRTUAL_DISPLAY = False

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.database import get_db_session
from src.models import Campaign, Card, Sector, Bank
from src.services.ai_parser import parse_api_campaign
from src.utils.slug_generator import generate_slug


class IsbankMaximilesScraper:
    """İşbankası Maximiles card campaign scraper"""
    
    BASE_URL = "https://www.maximiles.com.tr"
    CAMPAIGNS_URL = "https://www.maximiles.com.tr/kampanyalar"
    BANK_NAME = "İşbankası"
    CARD_NAME = "Maximiles"
    
    def __init__(self):
        self.driver = None
        self.display = None
        self.card_id = None
        self._init_card()
    
    def _init_card(self):
        """Get Maximiles card ID from database"""
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
        """Initialize Selenium driver"""
        if sys.platform.startswith('linux') and HAS_VIRTUAL_DISPLAY:
            print("   🖥️ Starting Virtual Display (Xvfb)...")
            try:
                self.display = Display(visible=0, size=(1920, 1080))
                self.display.start()
            except Exception as e:
                print(f"   ⚠️ Failed to start virtual display: {e}")

        if os.getenv('GITHUB_ACTIONS'):
            try:
                import undetected_chromedriver as uc
                options = uc.ChromeOptions()
                if not self.display:
                    options.add_argument('--headless=new') # Use new headless mode only if no display
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')
                # Add dummy user agent to prevent blocks in headless
                options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                
                # In Github Actions we let uc find the installed chrome
                driver = uc.Chrome(options=options)
                print("✅ Connected to undetected_chromedriver (GitHub Actions mode)")
                return driver
            except Exception as e:
                print(f"⚠️ Github Actions UC failed: {e}")
                # Fallback to standard selenium headless if UC completely fails
                try:
                    from selenium import webdriver
                    from selenium.webdriver.chrome.service import Service
                    from webdriver_manager.chrome import ChromeDriverManager
                    options = webdriver.ChromeOptions()
                    if not self.display:
                        options.add_argument('--headless=new')
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-dev-shm-usage')
                    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
                    print("✅ Connected to standard headless chrome (Fallback)")
                    return driver
                except Exception as e2:
                    raise Exception(f"All headless attempts failed. UC: {e}, Standard: {e2}")

        try:
            print("🚀 Launching new Chrome instance (Maximiles)...")
            import undetected_chromedriver as uc
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--start-maximized')
            
            try:
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
            time.sleep(5)
            return driver
        except Exception as e:
            print(f"⚠️ UC Launch failed: {e}")
            # Fallback to standard driver if needed, but UC is preferred
            return webdriver.Chrome()


    def _fetch_campaign_urls(self, limit: Optional[int] = None) -> List[str]:
        """Fetch all campaign URLs from the listing page."""
        print(f"📥 Fetching campaign list from {self.CAMPAIGNS_URL}...")
        
        self.driver.get(self.CAMPAIGNS_URL)
        time.sleep(10) # Increased wait for stability
        
        # Infinite scroll
        scroll_count = 0
        try:
            while True:
                if limit:
                    try:
                        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    except Exception as e:
                        print(f"   ⚠️ Error getting page source (window closed?): {e}")
                        break
                    count = len([a for a in soup.find_all('a', href=True) if '/kampanyalar/' in a['href'] 
                                 and 'arsiv' not in a['href'] 
                                 and not a['href'].endswith('-kampanyalari')
                                 and 'tum-kampanyalar' not in a['href']])
                    if count >= limit:
                        print(f"   ✅ Reached limit ({count} >= {limit}), stopping scroll.")
                        break
                
                scroll_count += 1
                try:
                    load_more_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Daha Fazla')]")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", load_more_btn)
                    time.sleep(1.5)
                    self.driver.execute_script("arguments[0].click();", load_more_btn)
                    time.sleep(2.5)
                    print(f"   ⏬ Loaded more campaigns (Scroll {scroll_count})...")
                except:
                    # Break if button not found
                    break
                
                if scroll_count > 50:
                    break

        except Exception as e:
            print(f"   ⚠️ Scroll loop ended/failed: {e}")
        
        # Extract campaign URLs
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        except:
             print("   ⚠️ Could not get page source.")
             return []

        excluded_slugs = [
            'gecmis-kampanyalar', 'arsiv', 'kampanyalar-arsivi'
        ]
        
        all_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Maximiles typically uses /kampanyalar/slug format
            if '/kampanyalar/' in href \
               and 'arsiv' not in href \
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
        """Extract campaign data from detail page."""
        try:
            self.driver.get(url)
            # Scroll to trigger lazy load
            self.driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(1.5)
            
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
                )
            except:
                pass
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Title
            title_el = soup.select_one('h1')
            title = self._clean_text(title_el.text) if title_el else "Başlık Yok"
            
            # Expiration checks
            if "gecmis" in url or "#gecmis" in url: return None
            if "geçmiş" in title.lower() or "süresi doldu" in title.lower(): return None

            # 1. Image (Background Image)
            image_url = None
            try:
                # The browser/selenium is needed to compute styles usually, but often it's inline or in a specific element
                # Agent found: section.campaign-banner
                banner_section = soup.select_one('section.campaign-banner')
                if banner_section and 'style' in banner_section.attrs:
                    style = banner_section['style']
                    # Extract url(...)
                    match = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style)
                    if match:
                         image_url = urljoin(self.BASE_URL, match.group(1))
                
                # Fallback: finding img directly if not background
                if not image_url:
                    img_el = soup.select_one('.campaign-detail-header img, section img')
                    if img_el and img_el.get('src') and 'logo' not in img_el['src']:
                        image_url = urljoin(self.BASE_URL, img_el['src'])
            except Exception as e:
                print(f"   ⚠️ Image extraction error: {e}")

            # 2. Date (Sidebar > Başlangıç - Bitiş Tarihi)
            date_text = ""
            # Look for the label text
            date_label = soup.find(string=re.compile(r"Başlangıç - Bitiş Tarihi"))
            if date_label:
                # usually the date is in the next sibling or parent's next sibling
                # Structure: <h6>Title</h6> <span>Date</span>
                parent = date_label.parent
                if parent:
                    # Check siblings
                    for sib in parent.next_siblings:
                        if sib.name and sib.get_text(strip=True):
                            date_text = self._clean_text(sib.get_text())
                            break
                    # If not found, check if it's inside the same parent
                    if not date_text:
                         date_text = self._clean_text(parent.get_text().replace(date_label, ''))
            
            # Fallback Date
            if not date_text:
                 date_candidates = [
                    soup.select_one(".campaign-date"),
                    soup.find("div", class_="date")
                ]
                 for c in date_candidates:
                     if c:
                         date_text = self._clean_text(c.text)
                         break

            # 3. Participation & Conditions
            participation_text = ""
            conditions = []
            full_text = ""

            # The main content is typically in the second section, left column
            # Structure seems to be: Section > Div.Container > Div.Row > Div.Col-Left (Text) | Div.Col-Right (Sidebar)
            
            # Let's find the main text container by looking for long text
            content_divs = soup.select('section div.container div.row div')
            # Filter for the one containing description text
            main_content_div = None
            max_len = 0
            
            for div in content_divs:
                text_len = len(div.get_text(strip=True))
                # Avoid the sidebar which matches "Başlangıç"
                if "Başlangıç - Bitiş Tarihi" not in div.get_text() and text_len > max_len:
                    max_len = text_len
                    main_content_div = div
            
            if main_content_div:
                 # Extract Participation specifically if labeled
                 part_label = main_content_div.find(string=re.compile(r"Katılım Şekli|Katılmak için", re.I))
                 if part_label:
                     # Get text around it
                     participation_text = self._clean_text(part_label.find_parent('p').get_text()) if part_label.find_parent('p') else ""
                 
                 # Clean up text for conditions
                 # Remove links like "tıklayınız" or simple navigation
                 for a in main_content_div.find_all('a'):
                     if 'tıklayınız' in a.get_text(): a.decompose()
                 
                 raw_text = main_content_div.get_text('\n')
                 conditions = [self._clean_text(line) for line in raw_text.split('\n') if len(self._clean_text(line)) > 20]
                 full_text = " ".join(conditions)
            else:
                # Fallback to body text
                 full_text = self._clean_text(soup.get_text())[:1000]

            if participation_text:
                full_text += f"\nKATILIM ŞEKLİ: {participation_text}"
            
            # Clean up unwanted default text from Maximiles site
            unwanted = ["Maximiles", "Maximiles Black", "MercedesCard", "Kampanyalar", "Kart Başvurusu Yap", "Giriş Yap"]
            conditions = [c for c in conditions if c not in unwanted and not c.startswith("Copyright")]

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
        if not date_text: return None
        text = date_text.replace('İ', 'i').lower().strip()
        
        try:
            # Pattern 1: DD.MM.YYYY - DD.MM.YYYY (Numeric Range)
            # Example: 01.02.2026 - 28.02.2026
            numeric_range_pattern = r'(\d{1,2})[./-](\d{1,2})[./-](\d{4})\s*-\s*(\d{1,2})[./-](\d{1,2})[./-](\d{4})'
            match = re.search(numeric_range_pattern, text)
            if match:
                d1, m1, y1, d2, m2, y2 = match.groups()
                if is_end: return f"{y2}-{m2.zfill(2)}-{d2.zfill(2)}"
                else: return f"{y1}-{m1.zfill(2)}-{d1.zfill(2)}"

            # Pattern 2: DD Month - DD Month YYYY (Textual Range)
            # Example: 1 Şubat - 28 Şubat 2026
            months = {'ocak': '01', 'şubat': '02', 'mart': '03', 'nisan': '04', 'mayıs': '05', 'haziran': '06', 
                      'temmuz': '07', 'ağustos': '08', 'eylül': '09', 'ekim': '10', 'kasım': '11', 'aralık': '12'}
            
            text_range_pattern = r'(\d{1,2})\s*([a-zğüşıöç]+)?\s*-\s*(\d{1,2})\s*([a-zğüşıöç]+)\s*(\d{4})'
            match = re.search(text_range_pattern, text)
            if match:
                day1, month1, day2, month2, year = match.groups()
                if not month1: month1 = month2
                
                m1_num = months.get(month1)
                m2_num = months.get(month2)
                
                if m1_num and m2_num:
                    if is_end: return f"{year}-{m2_num}-{str(day2).zfill(2)}"
                    else: return f"{year}-{m1_num}-{str(day1).zfill(2)}"
            
            # Pattern 3: Single Date (Numeric) DD.MM.YYYY
            # Example: 28.02.2026
            single_numeric = r'(\d{1,2})[./-](\d{1,2})[./-](\d{4})'
            match = re.search(single_numeric, text)
            if match:
                d, m, y = match.groups()
                return f"{y}-{m.zfill(2)}-{d.zfill(2)}"

        except Exception as e:
            print(f"   ⚠️ Date parsing error: {e}")
            pass
            
        return None
    
    def _clean_text(self, text: str) -> str:
        if not text: return ""
        text = text.replace('\n', ' ').replace('\r', '')
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _process_campaign(self, url: str):
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
            pass
        # ---------------------------------------------------------

        print(f"🔍 Processing: {url}")
        data = self._extract_campaign_data(url)
        if not data:
            print("   ⏭️  Skipped")
            return
        
        ai_result = parse_api_campaign(
            title=data['title'],
            short_description=data['full_text'][:500],
            content_html=data['full_text'],
            bank_name=self.BANK_NAME
        )
        self._save_campaign(data['title'], data['image_url'], data['date_text'], data['source_url'], ai_result)
    
    def _save_campaign(self, title: str, image_url: Optional[str], date_text: str, source_url: str, ai_data: Dict[str, Any]):
        print(f"   💾 Saving campaign: {title[:30]}...")
        try:
            with get_db_session() as db:
                from src.scrapers.isbankasi_maximiles import Campaign
                from src.models import Sector
                from src.utils.slug_generator import get_unique_slug
                
                # Check for existing campaign by slug + card_id first (to avoid re-inserting if run cleanly)
                # But since we have URL check, this is secondary.
                # We need a unique slug for INSERT.
                
                base_slug = generate_slug(ai_data.get('short_title') or title)
                # Ensure slug is unique globally
                slug = get_unique_slug(ai_data.get('short_title') or title, db, Campaign)
                
                sector_name = ai_data.get('sector', 'Diğer')
                sector = db.query(Sector).filter(Sector.name == sector_name).first()
                if not sector: sector = db.query(Sector).filter(Sector.slug == 'diger').first()
                
                start_date = None
                if ai_data.get('start_date'):
                    try: start_date = datetime.strptime(ai_data['start_date'], '%Y-%m-%d')
                    except: pass
                if not start_date:
                    sd_str = self._parse_date(date_text, is_end=False)
                    if sd_str:
                        try: start_date = datetime.strptime(sd_str, '%Y-%m-%d')
                        except: pass
                if not start_date: start_date = datetime.now()
                
                end_date = None
                if ai_data.get('end_date'):
                    try: end_date = datetime.strptime(ai_data['end_date'], '%Y-%m-%d')
                    except: pass
                if not end_date:
                    ed_str = self._parse_date(date_text, is_end=True)
                    if ed_str:
                        try: end_date = datetime.strptime(ed_str, '%Y-%m-%d')
                        except: pass
                
                conditions_lines = []
                participation = ai_data.get('participation')
                if participation and participation != "Detayları İnceleyin":
                    conditions_lines.append(f"KATILIM: {participation}")
                if ai_data.get('conditions'):
                    conditions_lines.extend(ai_data.get('conditions'))
                conditions_text = "\n".join(conditions_lines)
                
                eligible_cards_list = ai_data.get('cards', [])
                eligible_cards_str = ", ".join(eligible_cards_list) if eligible_cards_list else None
                
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
                
                 # Save Brands
                if ai_data.get('brands'):
                    from src.models import Brand, CampaignBrand
                    for brand_name in ai_data['brands']:
                        clean_name = brand_name.strip()
                        if not clean_name: continue
                        brand_slug = generate_slug(clean_name)
                        brand = db.query(Brand).filter(Brand.slug == brand_slug).first()
                        if not brand: brand = db.query(Brand).filter(Brand.name == clean_name).first()
                        if not brand:
                            brand = Brand(name=clean_name, slug=brand_slug, is_active=True, aliases=[clean_name])
                            db.add(brand)
                            db.flush()
                            print(f"      ✨ Created new brand: {clean_name}")
                        else:
                             print(f"      ✓ Brand exists: {clean_name}")
                        
                        db.flush()
                        existing_link = db.query(CampaignBrand).filter(CampaignBrand.campaign_id == campaign.id, CampaignBrand.brand_id == brand.id).first()
                        if not existing_link:
                            link = CampaignBrand(campaign_id=campaign.id, brand_id=brand.id)
                            db.add(link)
                            print(f"      🔗 Linked brand: {clean_name}")

                db.commit()
                print(f"   ✅ Saved: {campaign.title} (ID: {campaign.id})")
        except Exception as e:
            print(f"   ❌ Save Failed: {e}")
            import traceback
            traceback.print_exc()

    def run(self, limit: Optional[int] = None):
        try:
            print(f"🚀 Starting İşbankası Maximiles Scraper...")
            self.driver = self._get_driver()
            self.driver.set_page_load_timeout(60)
            urls = self._fetch_campaign_urls(limit=limit)
            for i, url in enumerate(urls, 1):
                print(f"\n[{i}/{len(urls)}]")
                self._process_campaign(url)
                time.sleep(1.5)
            print(f"\n🏁 Scraping finished. Processed {len(urls)} campaigns.")
        except Exception as e:
            print(f"❌ Scraper error: {e}")
            raise
        finally:
            if self.driver:
                try: self.driver.quit()
                except: pass
            if hasattr(self, 'display') and self.display:
                try: self.display.stop()
                except: pass

if __name__ == "__main__":
    scraper = IsbankMaximilesScraper()
    scraper.run()
