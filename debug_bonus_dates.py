
import sys
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Add src to path
sys.path.append(os.getcwd())

from src.scrapers.garanti_bonus import GarantiBonusScraper

class DebugBonusScraper(GarantiBonusScraper):
    def _process_campaign(self, url: str) -> bool:
        try:
            response = self.session.get(url, headers=self.HEADERS, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Title
            title_elm = soup.select_one('.campaign-detail-title h1')
            title = title_elm.get_text().strip() if title_elm else "Başlık Bulunamadı"
            
            print(f"\n🔍 Processing: {title[:50]}...")
            print(f"   URL: {url}")

            # 1. Dates from HTML (.campaign-date)
            date_elm = soup.select_one('.campaign-date')
            date_text = date_elm.get_text().strip() if date_elm else "NONE"
            print(f"   📄 HTML Date Text: '{date_text}'")
            
            # 2. Parse Logic
            start_date = None
            end_date = None
            if date_text and date_text != "NONE" and '-' in date_text:
                parts = date_text.split('-')
                if len(parts) >= 2:
                    # Try to parse end date first to get month/year context
                    end_part = parts[1].strip()
                    end_date = self._parse_turkish_date(end_part)
                    
                    start_part = parts[0].strip()
                    # specific handling for "1 - 28 Şubat 2026" where start is just a day
                    if start_part.isdigit() and end_date:
                        try:
                            day = int(start_part)
                            start_date = datetime(end_date.year, end_date.month, day)
                            print(f"   ✅ Range Parse Success: {start_date}")
                        except Exception as e:
                            print(f"   ❌ Range Parse Error for '{start_part}': {e}")
                            start_date = self._parse_turkish_date(start_part)
                    else:
                        start_date = self._parse_turkish_date(start_part)
            
            print(f"   🛠️ Parsed HTML Dates: Start={start_date}, End={end_date}")
            
            # 3. Fallback Logic Test
            if not start_date and end_date:
                print("   ⚠️ Start date missing. Applying fallback...")
                try:
                    start_today = datetime.utcnow().date()
                    if start_today <= end_date.date():
                        print(f"   ✅ Fallback: Set to Today ({start_today})")
                    else:
                        print(f"   ✅ Fallback: Set to End Date ({end_date.date()})")
                except:
                    pass

            return True
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

if __name__ == "__main__":
    print("🐞 Debugging Garanti Bonus Dates...")
    scraper = DebugBonusScraper()
    # Mock fetch to return just a few URLs causing issues or random ones
    scraper.CAMPAIGN_LIST_URL = 'https://www.bonus.com.tr/kampanyalar'
    
    # Let's run for 5 campaigns
    urls = scraper._fetch_campaign_list()[:5]
    
    for url in urls:
        scraper._process_campaign(url)
