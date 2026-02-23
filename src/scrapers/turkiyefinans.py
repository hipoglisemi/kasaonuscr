import os
import re
import sys
import time
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from services.ai_parser import AIParser
from services.brand_normalizer import cleanup_brands

# Selenium Imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

# --- CONFIG ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

BANK_NAME = "Türkiye Finans"
BANK_SLUG = "turkiye-finans"
BANK_LOGO = "https://www.turkiyefinans.com.tr/PublishingImages/Logo/tfkb-logo.png"

# Card definitions
CARD_DEFINITIONS = {
    "happy-card": {
        "name": "Happy Card", 
        "slug": "happy-card",
        "start_url": "https://www.happycard.com.tr/kampanyalar/Sayfalar/default.aspx",
        "domain": "https://www.happycard.com.tr"
    },
    "ala-card": {
        "name": "Âlâ Kart", 
        "slug": "ala-kart",
        "start_url": "https://www.turkiyefinansala.com/tr-tr/kampanyalar/Sayfalar/default.aspx",
        "domain": "https://www.turkiyefinansala.com"
    }
}

def slugify(text: str) -> str:
    text = text.lower()
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosucgiosu")
    text = text.translate(tr_map)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text).strip('-')
    return text

def html_to_text(html_content: str) -> str:
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    lines = [l.strip() for l in soup.get_text(separator="\n").splitlines() if l.strip()]
    return "\n".join(lines)

def filter_conditions(conditions: List[str]) -> List[str]:
    """Removes legal disclaimers and standard bank texts from conditions."""
    blacklist = [
        "değişiklik yapma hakkı", 
        "saklı tutar", 
        "yazım hataları", 
        "sorumlu tutulamaz", 
        "sorumluluk kabul edilmez",
        "banka kampanya şartlarını",
        "durdurma hakkına sahiptir",
        "sorumluluk türkiye finans"
    ]
    
    clean = []
    for c in conditions:
        c_lower = c.lower()
        # Check if the line contains any blacklisted phrase
        if any(b in c_lower for b in blacklist):
            continue
        clean.append(c)
    return clean

class TurkiyeFinansScraper:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.ai_parser = AIParser() if GEMINI_API_KEY else None
        self.bank_id = None
        self._card_cache = {}
        self.driver = None

    def setup_driver(self):
        """Initializes the Selenium WebDriver with robust options."""
        print("   🌐 Initializing Selenium WebDriver...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--dns-prefetch-disable")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.set_page_load_timeout(60)

    def teardown_driver(self):
        if self.driver:
            print("   🛑 Closing Selenium WebDriver...")
            self.driver.quit()
            self.driver = None

    def _get_or_create_bank(self):
        # ... (Same as before)
        try:
            with self.engine.begin() as conn:
                result = conn.execute(
                    text("SELECT id FROM banks WHERE slug = :slug"),
                    {"slug": BANK_SLUG}
                ).fetchone()
                if result:
                    self.bank_id = result[0]
                else:
                    print(f"   🏦 Creating Bank: {BANK_NAME}")
                    result = conn.execute(text("""
                        INSERT INTO banks (name, slug, logo_url, is_active, created_at)
                        VALUES (:name, :slug, :logo, true, NOW())
                        RETURNING id
                    """), {"name": BANK_NAME, "slug": BANK_SLUG, "logo": BANK_LOGO}).fetchone()
                    self.bank_id = result[0]
                print(f"   ✅ Bank ID: {self.bank_id}")
        except Exception as e:
            print(f"   ❌ Bank setup failed: {e}")
            raise

    def _get_or_create_card(self, card_def: dict) -> int:
        # ... (Same as before)
        slug = card_def["slug"]
        if slug in self._card_cache:
            return self._card_cache[slug]
        try:
            with self.engine.begin() as conn:
                result = conn.execute(
                    text("SELECT id FROM cards WHERE slug = :slug"),
                    {"slug": slug}
                ).fetchone()
                if result:
                    card_id = result[0]
                else:
                    print(f"   💳 Creating Card: {card_def['name']}")
                    result = conn.execute(text("""
                        INSERT INTO cards (name, slug, bank_id, card_type, is_active, created_at)
                        VALUES (:name, :slug, :bank_id, 'credit', true, NOW())
                        RETURNING id
                    """), {"name": card_def["name"], "slug": slug, "bank_id": self.bank_id}).fetchone()
                    card_id = result[0]
                self._card_cache[slug] = card_id
                return card_id
        except Exception as e:
            print(f"   ❌ Card setup failed: {e}")
            raise

    def _resolve_sector_by_name(self, sector_name: str) -> Optional[int]:
        if not sector_name: return None
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT id FROM sectors WHERE name ILIKE :name LIMIT 1"), {"name": f"%{sector_name}%"}).fetchone()
                return result[0] if result else None
        except Exception:
            return None

    def _collect_links(self, card_key: str) -> List[str]:
        card_def = CARD_DEFINITIONS[card_key]
        start_url = card_def["start_url"]
        domain = card_def["domain"]
        
        print(f"   🌐 [Selenium] Navigating to list page: {start_url}")
        links = set()
        
        try:
            if not self.driver:
                self.setup_driver()

            self.driver.get(start_url)
            time.sleep(5)
            
            # Scroll
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            anchors = self.driver.find_elements(By.TAG_NAME, "a")
            for a in anchors:
                try:
                    href = a.get_attribute("href")
                    if href:
                        if "/kampanyalar/" in href and "default.aspx" not in href.lower() and "spsdisco" not in href:
                             if domain in href or href.startswith("/"):
                                 if href.startswith("/"):
                                     if href.startswith(domain):
                                        links.add(href)
                                     else:
                                        links.add(f"{domain}{href}")
                                 else:
                                     links.add(href)
                except Exception: continue

            print(f"   ✅ Found {len(links)} links.")
        except Exception as e:
            print(f"   ❌ Link collection error: {e}")
            
        return sorted(list(links))

    def _process_campaign(self, url: str, card_key: str, card_id: int):
        card_def = CARD_DEFINITIONS[card_key]
        
        try:
            # Use Selenium for details too!
            self.driver.get(url)
            time.sleep(2) # Wait for dyn content
            
            # Get page source and parse with BS4 (easier to extract text than raw Selenium)
            html = self.driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            
            # Title Extraction
            title = ""
            GENERIC_TITLES = [
                "kampanyalar", "hesaplar", "yatırım hizmetleri", 
                "bankacılık hizmetleri", "âlâ kart", "âlâ hayat blog", 
                "kampanya detayı:", "sıkça sorulan sorular", "iletişim"
            ]

            h1 = soup.find("h1")
            if h1:
                t = h1.get_text(strip=True)
                if t and t.lower() not in GENERIC_TITLES: title = t

            if not title:
                h2 = soup.find("h2") 
                if h2: 
                    t = h2.get_text(strip=True)
                    if t and t.lower() not in GENERIC_TITLES: title = t

            if not title:
                if soup.title:
                    t = soup.title.string.replace("- Happy Card", "").replace("Türkiye Finans Happy Kredi Kartları Kampanyalar", "").strip()
                    if t and t.lower() not in GENERIC_TITLES: title = t
            
            if not title:
                h3 = soup.find("h3")
                if h3: 
                    t = h3.get_text(strip=True)
                    if t.lower() not in GENERIC_TITLES: title = t
            
            if not title or title.lower() in GENERIC_TITLES:
                 print(f"      ⚠️ Valid title not found, skipping {url}")
                 return

            # Image
            image_url = None
            img_tag = soup.select_one(".campaign-image img") or \
                      soup.select_one(".ms-rteImage-4") or \
                      soup.select_one("img[src*='upload']") or \
                      soup.select_one("img[src*='banner']") or \
                      soup.select_one("img[src*='kampanya']")
            if img_tag:
                src = img_tag.get("src")
                if src:
                    if src.startswith("http"): image_url = src
                    elif src.startswith("/"): image_url = f"{card_def['domain']}{src}"

            # Content - Best Candidate Strategy
            candidates = []
            candidates.extend(soup.select(".ms-rtestate-field"))
            candidates.extend(soup.select(".campaign-description"))
            candidates.extend(soup.select(".campaign-text")) # Added based on debug
            candidates.extend(soup.select("#content"))
            candidates.extend(soup.select(".content"))
            
            content_text = ""
            max_len = 0

            # Find the candidate with the most text
            for cand in candidates:
                txt = html_to_text(str(cand))
                # Basic cleanup check
                if len(txt) > max_len:
                    max_len = len(txt)
                    content_text = txt
            
            # Fallback to body only if candidates failed completely or returned very short text
            if max_len < 100:
                print("      ⚠️ Candidate text too short, trying Body fallback...")
                # Body fallback with aggressive cleanup
                body_copy = soup.body
                if body_copy:
                    # Remove known clutter
                    for tag in body_copy.select("nav, footer, header, .menu, .sidebar, script, style, noscript, .ms-webpart-zone, .search-box"):
                        tag.decompose()
                    body_text = html_to_text(str(body_copy))
                    if len(body_text) > max_len:
                        content_text = body_text

            if len(content_text) < 50:
                 print(f"      ⚠️ Content too short ({len(content_text)} chars), might be empty.")

            # AI Parsing
            ai_data = {}
            if self.ai_parser and content_text:
                try:
                    ai_data = self.ai_parser.parse_campaign_data(
                        raw_text=content_text,
                        title=title,
                        bank_name=BANK_NAME,
                        card_name=card_def["name"],
                    )
                except Exception as e:
                    print(f"      ⚠️  AI Error: {e}")

            # Slug
            link_slug = slugify(url.rstrip("/").split("/")[-1].replace(".aspx",""))
            if not link_slug or link_slug == "default": link_slug = slugify(title)
            slug = f"{link_slug}-{int(time.time())}"

            conditions_lines = []
            participation = ai_data.get("participation")
            if participation: conditions_lines.append(f"KATILIM: {participation}")
            
            eligible_cards = ai_data.get("cards")
            eligible_str = ", ".join(eligible_cards) if eligible_cards else None
            if eligible_str and len(eligible_str) > 255: eligible_str = eligible_str[:255]
            
            conditions_lines.extend(ai_data.get("conditions", []))
            
            # Filter unwanted legal text
            conditions_lines = filter_conditions(conditions_lines)
            
            # Database Ops
            with self.engine.begin() as conn:
                existing = conn.execute(text("SELECT id FROM campaigns WHERE tracking_url = :url"), {"url": url}).fetchone()
                
                campaign_data = {
                    "title": ai_data.get("title") or title,
                    "description": ai_data.get("description") or "",
                    "image_url": image_url,
                    "tracking_url": url,
                    "start_date": ai_data.get("start_date"),
                    "end_date": ai_data.get("end_date"),
                    "sector_id": self._resolve_sector_by_name(ai_data.get("sector")) or self._resolve_sector_by_name("Diğer"),
                    "card_id": card_id,
                    "conditions": "\n".join(conditions_lines) if conditions_lines else None,
                    "eligible_cards": eligible_str,
                    "reward_text": ai_data.get("reward_text"),
                    "reward_value": ai_data.get("reward_value"),
                    "reward_type": ai_data.get("reward_type"),
                }

                if existing:
                    print(f"   🔄 Updating: {title[:40]}")
                    conn.execute(text("""
                        UPDATE campaigns
                        SET title=:title, description=:description, image_url=:image_url,
                            start_date=:start_date, end_date=:end_date, sector_id=:sector_id,
                            conditions=:conditions, eligible_cards=:eligible_cards,
                            reward_text=:reward_text, reward_value=:reward_value,
                            reward_type=:reward_type, updated_at=NOW()
                        WHERE tracking_url=:tracking_url
                    """), campaign_data)
                    campaign_id = existing[0]
                else:
                    print(f"   ✨ Creating: {title[:40]}")
                    campaign_data["slug"] = slug
                    result = conn.execute(text("""
                        INSERT INTO campaigns (
                            title, description, slug, image_url, tracking_url, is_active,
                            sector_id, card_id, start_date, end_date, conditions,
                            eligible_cards, reward_text, reward_value, reward_type,
                            created_at, updated_at
                        )
                        VALUES (
                            :title, :description, :slug, :image_url, :tracking_url, true,
                            :sector_id, :card_id, :start_date, :end_date, :conditions,
                            :eligible_cards, :reward_text, :reward_value, :reward_type,
                            NOW(), NOW()
                        )
                        RETURNING id
                    """), campaign_data)
                    campaign_id = result.fetchone()[0]

                # Brands (unchanged logic)
                if ai_data.get("brands") and campaign_id:
                    clean_brands = cleanup_brands(ai_data["brands"])
                    for brand_name in clean_brands:
                        brand_res = conn.execute(text("SELECT id FROM brands WHERE name=:name"), {"name": brand_name}).fetchone()
                        if brand_res:
                            bid = brand_res[0]
                        else:
                            bslug = f"{slugify(brand_name)}-{int(time.time())}"
                            brand_res = conn.execute(text("INSERT INTO brands (name, slug, is_active, created_at) VALUES (:name, :slug, true, NOW()) RETURNING id"), {"name": brand_name, "slug": bslug}).fetchone()
                            bid = brand_res[0]
                        
                        link_check = conn.execute(text("SELECT 1 FROM campaign_brands WHERE campaign_id=:cid AND brand_id=CAST(:bid AS uuid)"), {"cid": campaign_id, "bid": bid}).fetchone()
                        if not link_check:
                            conn.execute(text("INSERT INTO campaign_brands (campaign_id, brand_id) VALUES (:cid, CAST(:bid AS uuid))"), {"cid": campaign_id, "bid": bid})

        except Exception as e:
            print(f"   ❌ Error processing {url}: {e}")

    def run(self, limit: int = 1000, target: str = "all"):
        print("🚀 Starting Türkiye Finans Scraper (Full Selenium)...")
        self._get_or_create_bank()
        
        cards_to_process = []
        if target == "all": cards_to_process = ["happy-card", "ala-card"]
        else: cards_to_process = [target]

        try:
            self.setup_driver()
            
            for card_key in cards_to_process:
                card_def = CARD_DEFINITIONS[card_key]
                print(f"\n👉 Processing {card_def['name']}...")
                card_id = self._get_or_create_card(card_def)
                
                links = self._collect_links(card_key)
                if not links: continue
                    
                links_to_process = links[:limit]
                print(f"   🎯 Detailed processing for {len(links_to_process)} campaigns...")
                
                for idx, url in enumerate(links_to_process):
                    print(f"[{idx+1}/{len(links_to_process)}] {url}")
                    self._process_campaign(url, card_key, card_id)
        
        finally:
            self.teardown_driver()
            print("\n🏁 Türkiye Finans Scraper Finished.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--target", type=str, default="all")
    args = parser.parse_args()

    scraper = TurkiyeFinansScraper()
    scraper.run(limit=args.limit, target=args.target)
