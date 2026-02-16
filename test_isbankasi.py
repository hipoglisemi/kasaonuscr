#!/usr/bin/env python
"""
Test script for İşbankası Maximum scraper

IMPORTANT: Before running this script, start Chrome in debug mode:
/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome_dev_test"
"""

from src.scrapers.isbankasi_maximum import IsbankMaximumScraper

if __name__ == "__main__":
    print("🧪 Testing İşbankası Maximum Scraper...")
    print("📝 Will scrape 2 campaigns for verification\n")
    
    scraper = IsbankMaximumScraper()
    # We want to see the AI output, so we rely on the scraper's print statements
    # But let's check the DB after run? Or just trust the logs which show "Saving campaign..."
    scraper.run(limit=5)
    
    print("\n✅ Test completed!")
