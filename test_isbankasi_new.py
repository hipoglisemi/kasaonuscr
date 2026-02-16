
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
    print("🧪 Testing Maximiles Scraper...")
    print("="*50)
    try:
        scraper = IsbankMaximilesScraper()
        scraper.run(limit=5)
        print("\n✅ Maximiles Test Completed!")
    except Exception as e:
        print(f"\n❌ Maximiles Test Failed: {e}")

def test_genc():
    kill_chrome()
    print("\n" + "="*50)
    print("⏳ Waiting 20s before starting next test...")
    time.sleep(20)
    print("🧪 Testing Maximum Genç Scraper...")
    print("="*50)
    try:
        scraper = IsbankMaximumGencScraper()
        scraper.run(limit=5)
        print("\n✅ Maximum Genç Test Completed!")
    except Exception as e:
        print(f"\n❌ Maximum Genç Test Failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Verification for New Scrapers...")
    
    test_maximiles()
    test_genc()
    
    print("\n🏁 All tests finished.")
