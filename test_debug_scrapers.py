
import sys
import os
import time
import subprocess

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.scrapers.isbankasi_maximiles import IsbankMaximilesScraper
from src.scrapers.isbankasi_genc import IsbankMaximumGencScraper

def kill_chrome():
    print("🧹 Killing conflicting Chrome processes...")
    try:
        subprocess.run(["pkill", "-f", "Google Chrome"], stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-f", "undetected_chromedriver"], stderr=subprocess.DEVNULL)
        time.sleep(2)
    except:
        pass

def test_maximiles():
    kill_chrome()
    time.sleep(2)
    print("\n" + "="*50)
    print("🧪 Testing Maximiles Scraper (Debug)...")
    print("="*50)
    try:
        scraper = IsbankMaximilesScraper()
        # Override process_campaign to just print data
        original_process = scraper._process_campaign
        
        def debug_process(url):
            print(f"🔍 Debugging: {url}")
            data = scraper._extract_campaign_data(url)
            if data:
                print(f"   📌 Title: {data.get('title')}")
                print(f"   🖼️ Image: {data.get('image_url')}")
                print(f"   📅 Date: {data.get('date_text')}")
                print(f"   🤝 Participation: {data.get('participation')}")
                print(f"   📝 Conditions (First 2 lines): {data.get('conditions', [])[:2]}")
                print("-" * 30)
            else:
                print("   ❌ Failed to extract data")
        
        scraper._process_campaign = debug_process
        scraper.run(limit=5)
        print("\n✅ Maximiles Debug Test Completed!")
    except Exception as e:
        print(f"\n❌ Maximiles Test Failed: {e}")

def test_genc():
    kill_chrome()
    print("\n" + "="*50)
    print("⏳ Waiting 10s before starting next test...")
    time.sleep(10)
    print("🧪 Testing Maximum Genç Scraper (Debug)...")
    print("="*50)
    try:
        scraper = IsbankMaximumGencScraper()
        # Override process_campaign to just print data
        original_process = scraper._process_campaign
        
        def debug_process(campaign_data):
            url = campaign_data['url']
            img = campaign_data.get('image_url')
            print(f"🔍 Debugging: {url}")
            data = scraper._extract_campaign_data(url, img)
            if data:
                print(f"   📌 Title: {data.get('title')}")
                print(f"   🖼️ Image: {data.get('image_url')}")
                print(f"   📅 Date: {data.get('date_text')}")
                print(f"   🤝 Participation: {data.get('participation')}")
                print(f"   📝 Conditions (First 2 lines): {data.get('conditions', [])[:2]}")
                print("-" * 30)
            else:
                print("   ❌ Failed to extract data")
        
        scraper._process_campaign = debug_process
        scraper.run(limit=5)
        print("\n✅ Maximum Genç Debug Test Completed!")
    except Exception as e:
        print(f"\n❌ Maximum Genç Test Failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Debug Verification...")
    
    test_maximiles()
    test_genc()
    
    print("\n🏁 All tests finished.")
