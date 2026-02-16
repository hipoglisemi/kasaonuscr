
import os
import time
import random
import re
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import sys

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Database
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import JSONB

# AI
import google.generativeai as genai
from services.ai_parser import AIParser

# Browser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth

# Virtual Display (for GitHub Actions / Headless)
try:
    from pyvirtualdisplay import Display
    HAS_VIRTUAL_DISPLAY = True
except ImportError:
    HAS_VIRTUAL_DISPLAY = False

load_dotenv()

# --- CONFIG ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env")

# AI Config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️ GEMINI_API_KEY not found. AI parsing will be disabled/mocked.")

# ZenRows API Key (Optional - for Proxy Bypass)
ZENROWS_API_KEY = os.getenv("ZENROWS_API_KEY")

# Constants
BLACKLIST_IMAGES = [
    "denizbank-logo", "campaign-default", "placeholder", 
    "transparent.png", "blank.gif"
]

class DenizbankScraper:
    BASE_URL = "https://www.denizbonus.com"
    CAMPAIGNS_URL = "https://www.denizbonus.com/bonus-kampanyalari"

    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        if GEMINI_API_KEY:
            self.ai_parser = AIParser(GEMINI_API_KEY)
        else:
            self.ai_parser = None
            
        self.driver = None
        self.display = None

    def setup_driver(self):
        """Initialize Selenium with Stealth."""
        if self.driver:
            return

        # Start Virtual Display if on Linux/Server and no ZenRows
        if sys.platform.startswith('linux') and HAS_VIRTUAL_DISPLAY and not ZENROWS_API_KEY:
            print("   🖥️ Starting Virtual Display (Xvfb)...")
            try:
                self.display = Display(visible=0, size=(1920, 1080))
                self.display.start()
            except Exception as e:
                print(f"   ⚠️ Failed to start virtual display: {e}")

        print("   🔌 Initializing Browser Driver (Selenium Stealth)...")
        options = webdriver.ChromeOptions()
        
        # Performance & Stability
        options.page_load_strategy = 'eager'
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--window-size=1920,1080")
        
        # Anti-Detection Args
        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Apply Stealth
            stealth(self.driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            
            print("   ✅ Browser launched successfully.")
        except Exception as e:
            print(f"   ❌ Failed to launch browser: {e}")
            raise e

    def close_driver(self):
        if self.driver:
            print("   🛑 Closing Browser...")
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            
        if self.display:
            try:
                self.display.stop()
            except:
                pass
            self.display = None

    def _fetch_html(self, url):
        """Fetch HTML. Uses ZenRows if Key exists, otherwise Selenium Stealth."""
        
        # --- MODE 1: ZenRows Proxy (Reliable) ---
        if ZENROWS_API_KEY:
            try:
                print(f"   🛡️ Fetching via ZenRows Proxy: {url}")
                proxy_url = "https://api.zenrows.com/v1/"
                params = {
                    "apikey": ZENROWS_API_KEY,
                    "url": url,
                    "js_render": "true",
                    "premium_proxy": "true", # Optional, helps with banking sites
                }
                response = requests.get(proxy_url, params=params, timeout=60)
                if response.status_code == 200:
                    return response.text
                else:
                    print(f"   ❌ ZenRows Error: {response.status_code} - {response.text}")
                    return None
            except Exception as e:
                print(f"   ❌ ZenRows Exception: {e}")
                return None

        # --- MODE 2: Selenium Stealth (Free / Direct) ---
        self.setup_driver()
        try:
            print(f"   🌐 Navigating (Direct): {url}")
            self.driver.get(url)
            
            # Random sleep & Scroll
            time.sleep(random.uniform(3.0, 6.0))
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(1)
            
            return self.driver.page_source
            
        except Exception as e:
            print(f"   ❌ Browser navigation failed: {e}")
            self.close_driver()
            return None

    def _get_slug(self, title):
        slug = title.lower()
        replacements = {
            'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c',
            'İ': 'i', 'Ğ': 'g', 'Ü': 'u', 'Ş': 's', 'Ö': 'o', 'Ç': 'c'
        }
        for src, dest in replacements.items():
            slug = slug.replace(src, dest)
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        return slug.strip('-')

    def _fetch_campaign_list(self, limit=None):
        html = self._fetch_html(self.CAMPAIGNS_URL)
        if not html:
            print("   ❌ Failed to fetch campaign list.")
            return []

        soup = BeautifulSoup(html, 'html.parser')
        campaign_urls = []
        
        links = soup.find_all('a', href=True)
        unique_urls = set()
        
        for link in links:
            href = link['href']
            if '/kampanyalar/' in href and href.count('/') > 2: 
                full_url = href if href.startswith('http') else self.BASE_URL + href
                unique_urls.add(full_url)

        campaign_urls = list(unique_urls)
        print(f"   🎉 Found {len(campaign_urls)} campaigns via scraping.")
        
        if limit and len(campaign_urls) > limit:
            campaign_urls = campaign_urls[:limit]
            
        return campaign_urls

    def _process_campaign(self, url):
        print(f"🔍 Processing: {url}")
        html = self._fetch_html(url)
        if not html:
            print("   ❌ Skipping (No HTML)")
            return

        soup = BeautifulSoup(html, 'html.parser')

        title = "Kampanya Detayı"
        meta_title = soup.find("meta", property="og:title")
        if meta_title: title = meta_title.get("content", "").strip()
        else:
            h1 = soup.find('h1')
            if h1: title = h1.get_text(strip=True)

        description = ""
        meta_desc = soup.find("meta", property="og:description")
        if meta_desc: description = meta_desc.get("content", "").strip()
        
        main_content = soup.find('div', class_=re.compile(r'detail|content|campaign'))
        raw_text = main_content.get_text(separator="\n", strip=True) if main_content else soup.body.get_text()

        image_url = ""
        meta_image = soup.find("meta", property="og:image")
        if meta_image: image_url = meta_image.get("content", "")
        
        if not image_url or any(x in image_url for x in BLACKLIST_IMAGES):
            images = soup.find_all('img', src=True)
            for img in images:
                src = img['src']
                if not any(x in src for x in BLACKLIST_IMAGES) and len(src) > 20:
                    image_url = src if src.startswith('http') else self.BASE_URL + src
                    break

        brand = "DenizBonus"
        if "troy" in title.lower(): brand = "DenizBank TROY"
        if "black" in title.lower(): brand = "DenizBank Black"
        
        slug = self._get_slug(title)
        
        campaign_data = {
            "title": title,
            "description": description,
            "content": raw_text[:3000],
            "image_url": image_url,
            "start_date": None,
            "end_date": None,
            "slug": slug,
            "brand": brand,
            "is_active": True,
            "sector_id": "genel",
            "tracking_url": url
        }

        self._save_to_db(campaign_data)

    def _save_to_db(self, data):
        try:
            with self.engine.begin() as conn:
                existing = conn.execute(
                    text("SELECT id FROM campaigns WHERE tracking_url = :url"),
                    {"url": data['tracking_url']}
                ).fetchone()

                if existing:
                    print(f"   🔄 Updating: {data['title']}")
                    conn.execute(
                        text("""
                            UPDATE campaigns 
                            SET title=:title, description=:description, image_url=:image_url, updated_at=NOW()
                            WHERE tracking_url=:url
                        """),
                        {"title": data['title'], "description": data['description'], "image_url": data['image_url'], "url": data['tracking_url']}
                    )
                else:
                    print(f"   ✨ Creating: {data['title']}")
                    conn.execute(
                        text("""
                            INSERT INTO campaigns (title, description, slug, image_url, tracking_url, brand, is_active, sector_id)
                            VALUES (:title, :description, :slug, :image_url, :url, :brand, true, :sector)
                        """), data
                    )
        except Exception as e:
            print(f"   ❌ DB Error: {e}")

    def run(self):
        print("🚀 Starting Denizbank Hybrid Scraper...")
        if ZENROWS_API_KEY:
            print("   💎 Mode: Proxy API (ZenRows)")
        else:
            print("   🆓 Mode: Direct Selenium (Stealth)")
            
        try:
            urls = self._fetch_campaign_list()
            print(f"   🎯 Processing {len(urls)} campaigns...")
            
            for i, url in enumerate(urls):
                if i >= 20: 
                    print("   ⚠️ Reached limit of 20 for this run.")
                    break
                self._process_campaign(url)
                # Sleep more if in free mode
                if not ZENROWS_API_KEY:
                    time.sleep(3)
                    
        finally:
            self.close_driver()
            print("🏁 Scraper Finished.")

if __name__ == "__main__":
    scraper = DenizbankScraper()
    scraper.run()
