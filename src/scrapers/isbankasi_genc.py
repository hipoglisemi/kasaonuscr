"""
İşbankası Maximum Genç Scraper
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


class IsbankMaximumGencScraper:
    """İşbankası Maximum Genç card campaign scraper"""
    
    BASE_URL = "https://www.maximumgenc.com.tr"
    CAMPAIGNS_URL = "https://www.maximumgenc.com.tr/kampanyalar"
    BANK_NAME = "İşbankası"
    CARD_NAME = "Maximum Genç"
    
    def __init__(self):
        self.driver = None
        self.card_id = None
        self._init_card()
    
    def _init_card(self):
        """Get Maximum Genç card ID from database"""
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
        """Initialize Selenium driver - Using same robust logic as Maximiles"""
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

        try:
            print("🚀 Launching new Chrome instance (Maximum Genç) - Standard Driver...")
            options = webdriver.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--start-maximized')
            options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Using standard chromedriver
            driver = webdriver.Chrome(options=options)
            
            print("✅ Launched new standard Chrome instance successfully!")
            time.sleep(2)
            return driver
        except Exception as e:
            print(f"⚠️ Standard Launch failed: {e}")
            raise


    def _fetch_campaign_urls(self, limit: Optional[int] = None) -> List[str]:
        """Fetch all campaign URLs from the listing page."""
        print(f"📥 Fetching campaign list from {self.CAMPAIGNS_URL}...")
        
        self.driver.get(self.CAMPAIGNS_URL)
        time.sleep(10) # Increased wait for stability
        
        # Infinite scroll
        scroll_count = 0
        max_scrolls = 100
        
        try:
            while True:
                if limit and limit > 0:
                    try:
                        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                        count = len([a for a in soup.find_all('a', href=True) 
                                     if '/kampanyalar/' in a['href'] 
                                     and 'gecmis' not in a['href']])
                        if count >= limit:
                            print(f"   ✅ Reached limit ({count} >= {limit}), stopping scroll.")
                            break
                    except Exception as e:
                        print(f"   ⚠️ Error counting items: {e}")

                scroll_count += 1
                if scroll_count > max_scrolls:
                    print("   ⚠️ Max scrolls reached.")
                    break

                try:
                    # Scroll to bottom first to trigger potential visibility
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    
                    # Try to find "Daha Fazla" button
                    load_more_btn = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".show-more-opportunity"))
                    )
                    
                    if load_more_btn.is_displayed():
                        # Try JS click to bypass overlays
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", load_more_btn)
                        time.sleep(1)
                        try:
                            self.driver.execute_script("arguments[0].click();", load_more_btn)
                        except:
                            load_more_btn.click()
                        
                        time.sleep(3) # Wait for content load
                        print(f"   ⏬ Loaded more campaigns (Scroll {scroll_count})...")
                    else:
                        print(f"   ℹ️ Load more button present but hidden (Scroll {scroll_count})")
                        if scroll_count > 1: # Give it a chance if it's just loading
                            break
                except Exception as e:
                    # Button not found - usually means end of list
                    print(f"   ℹ️ Load more button not found (End of list?): {e}")
                    break
                
        except Exception as e:
            print(f"   ⚠️ Scroll loop ended/failed: {e}")
        
        # Extract campaign URLs
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        except:
             print("   ⚠️ Could not get page source.")
             return []

        excluded_keywords = ['gecmis', 'arsiv', 'tum-kampanyalar'] 
        
        all_links = []
        found_count = 0
        skipped_count = 0
        
        # Target specific campaign cards
        cards = soup.select('.opportunity-result a')
        print(f"   ℹ️ Found {len(cards)} campaign cards in DOM")

        for a in cards:
            href = a.get('href')
            if not href: continue
             
            # Debug logging
            is_excluded = any(ex in href for ex in excluded_keywords)
            
            # Additional check: exclude javascript: links
            if 'javascript' in href: is_excluded = True

            if is_excluded:
                skipped_count += 1
            else:
                full_url = urljoin(self.BASE_URL, href)
                all_links.append(full_url)
                found_count += 1
        
        # Also try broad search as fallback if specific selector failed (e.g. layout change)
        if len(all_links) == 0:
             print("   ⚠️ No cards found with .opportunity-result, trying broad search...")
             for a in soup.find_all('a', href=True):
                href = a['href']
                if '/kampanyalar/' in href and not any(ex in href for ex in excluded_keywords):
                     full_url = urljoin(self.BASE_URL, href)
                     all_links.append(full_url)

        unique_urls = list(dict.fromkeys(all_links))
        
        print(f"   ℹ️ Links extracted: {len(unique_urls)}, Skipped: {skipped_count}")
        
        if limit and limit > 0:
            unique_urls = unique_urls[:limit]
        
        print(f"✅ Found {len(unique_urls)} unique campaigns to process")
        return unique_urls
    
    # Fallback image if scraping fails
    DEFAULT_IMAGE_URL = "https://www.maximumgenc.com.tr/_assets/images/logo.png"

    def _extract_campaign_data(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract campaign data from detail page using a NEW TAB strategy."""
        original_window = self.driver.current_window_handle
        new_window = None
        
        try:
            # Open new tab
            self.driver.execute_script(f"window.open('{url}', '_blank');")
            time.sleep(1)
            
            # Switch to new tab
            new_window = [w for w in self.driver.window_handles if w != original_window][-1]
            self.driver.switch_to.window(new_window)
            
            # Wait for content
            try:
                # Scroll to trigger lazy load
                self.driver.execute_script("window.scrollTo(0, 500);")
                time.sleep(2.5)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
                )
            except:
                print("   ⚠️ Page load timeout/error")
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Title
            title_el = soup.select_one('h1')
            title = self._clean_text(title_el.text) if title_el else "Başlık Yok"
            
            # Expiration checks
            if "gecmis" in url or "#gecmis" in url or "geçmiş" in title.lower() or "süresi doldu" in title.lower():
                return None

            # 1. Image (with Fallback)
            image_url = None
            try:
                # Genç often uses header image or section image
                img_el = soup.select_one('.detail-img img') or soup.select_one('section img')
                if img_el and img_el.get('src'):
                    image_url = urljoin(self.BASE_URL, img_el['src'])
                
                # Check background image style if needed
                if not image_url:
                     banner_section = soup.select_one('section.banner, div.banner')
                     if banner_section and 'style' in banner_section.attrs:
                        style = banner_section['style']
                        match = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style)
                        if match:
                             image_url = urljoin(self.BASE_URL, match.group(1))

            except Exception as e:
                print(f"   ⚠️ Image extraction error: {e}")
            
            # Use Fallback if no image found
            if not image_url:
                print("   ⚠️ No image found, using default fallback.")
                image_url = self.DEFAULT_IMAGE_URL

            # 2. Date
            date_text = ""
            date_el = soup.select_one(".date, .campaign-date")
            if date_el:
                date_text = self._clean_text(date_el.text)
            
            # Fallback Date: Look for text pattern
            if not date_text:
                full_page_text = soup.get_text()
                date_match = re.search(r'(\d{1,2}\s+[a-zA-ZğüşıöçĞÜŞİÖÇ]+\s+\d{4})\s*-\s*(\d{1,2}\s+[a-zA-ZğüşıöçĞÜŞİÖÇ]+\s+\d{4})', full_page_text)
                if date_match:
                    date_text = date_match.group(0)

            # 3. Participation & Conditions
            participation_text = ""
            conditions = []
            full_text = ""

            # Try to find content div
            content_div = soup.select_one('.detail-text, .campaign-content, section .container')
            if content_div:
                 # Extract Participation
                 part_label = content_div.find(string=re.compile(r"Katılım Şekli|Katılmak için", re.I))
                 if part_label:
                     parent = part_label.find_parent('p') or part_label.find_parent('div')
                     participation_text = self._clean_text(parent.get_text()) if parent else ""
                 
                 # Conditions
                 raw_text = content_div.get_text('\n')
                 conditions = [self._clean_text(line) for line in raw_text.split('\n') if len(self._clean_text(line)) > 20]
                 full_text = " ".join(conditions)
            else:
                 full_text = self._clean_text(soup.get_text())[:1000]

            if participation_text:
                full_text += f"\nKATILIM ŞEKLİ: {participation_text}"
            
            conditions = [c for c in conditions if not c.startswith("Copyright")]

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
        finally:
            # Always close the new tab and switch back
            if new_window:
                try:
                    self.driver.close()
                except:
                    pass
            try:
                self.driver.switch_to.window(original_window)
            except:
                pass
    
    def _parse_date(self, date_text: str, is_end: bool = False) -> Optional[str]:
        """Parse Turkish date format to YYYY-MM-DD"""
        if not date_text: return None
        text = date_text.replace('İ', 'i').lower()
        months = {'ocak': '01', 'şubat': '02', 'mart': '03', 'nisan': '04', 'mayıs': '05', 'haziran': '06', 
                  'temmuz': '07', 'ağustos': '08', 'eylül': '09', 'ekim': '10', 'kasım': '11', 'aralık': '12'}
        try:
            pattern = r'(\d{1,2})\s*([a-zğüşıöç]+)?\s*-\s*(\d{1,2})\s*([a-zğüşıöç]+)\s*(\d{4})'
            match = re.search(pattern, text)
            if match:
                day1, month1, day2, month2, year = match.groups()
                if not month1: month1 = month2
                if is_end: return f"{year}-{months.get(month2, '12')}-{str(day2).zfill(2)}"
                else: return f"{year}-{months.get(month1, '01')}-{str(day1).zfill(2)}"
        except: pass
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
        # Note: _extract_campaign_data now handles tab management internally
        data = self._extract_campaign_data(url)
        
        if not data:
            print("   ⏭️  Skipped (No data or closed window)")
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
                from src.models import Sector, CampaignBrand, Brand
                from src.utils.slug_generator import get_unique_slug
                
                base_slug = generate_slug(ai_data.get('short_title') or title)
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
            print(f"🚀 Starting İşbankası Maximum Genç Scraper...")
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

if __name__ == "__main__":
    scraper = IsbankMaximumGencScraper()
    scraper.run(limit=5)
