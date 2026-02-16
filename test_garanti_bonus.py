#!/usr/bin/env python3
"""
Test script for Garanti Bonus scraper
Scrapes only 5 campaigns to local database for testing
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.garanti_bonus import GarantiBonusScraper

def main():
    print("🧪 Testing Garanti Bonus Scraper (5 campaigns)")
    print("=" * 60)
    
    scraper = GarantiBonusScraper()
    
    # Override _fetch_campaign_list to limit to 5
    original_fetch = scraper._fetch_campaign_list
    
    def limited_fetch():
        urls = original_fetch()
        print(f"📊 Total campaigns available: {len(urls)}")
        print(f"🎯 Limiting to first 5 for testing...")
        return urls[:5]
    
    scraper._fetch_campaign_list = limited_fetch
    
    # Run scraper
    scraper.run()
    
    print("\n" + "=" * 60)
    print("✅ Test complete! Check your database for 5 new campaigns.")

if __name__ == "__main__":
    main()
