#!/usr/bin/env python3
"""
Fresh Scrape Script for Kartavantaj
Deletes all campaigns and scrapes 10 from each scraper
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import get_db_session
from src.models import Campaign


def delete_all_campaigns():
    """Delete all campaigns from database"""
    print("🗑️  Deleting all campaigns from database...\n")
    
    session = get_db_session()
    
    try:
        # Get count
        count = session.query(Campaign).count()
        
        print(f"📊 Found {count} campaigns to delete\n")
        
        if count == 0:
            print("✅ No campaigns to delete!")
            session.close()
            return True
        
        print("⚠️  WARNING: This will delete ALL campaigns!")
        print("   Proceeding in 3 seconds...\n")
        time.sleep(3)
        
        # Delete all campaigns
        session.query(Campaign).delete()
        session.commit()
        
        print(f"✅ Successfully deleted {count} campaigns!\n")
        session.close()
        return True
    except Exception as e:
        print(f"❌ Error deleting campaigns: {e}")
        session.rollback()
        session.close()
        return False


def run_scraper(scraper_name, scraper_file, limit=10):
    """Run a single scraper with limit"""
    print(f"   🚀 Running {scraper_name}...")
    
    try:
        # Run scraper with limit
        result = subprocess.run(
            ['python3', f'src/scrapers/{scraper_file}', '--limit', str(limit)],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per scraper
        )
        
        if result.returncode == 0:
            print(f"   ✅ {scraper_name} completed successfully!")
            return True
        else:
            print(f"   ❌ {scraper_name} failed:")
            print(f"      {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"   ⏱️  {scraper_name} timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"   ❌ {scraper_name} error: {str(e)[:200]}")
        return False

def main():
    print("━" * 80)
    print("🚀 KARTAVANTAJ FRESH SCRAPE: 10 Campaigns Per Scraper")
    print("━" * 80)
    print()
    
    # Step 1: Delete all campaigns
    if not delete_all_campaigns():
        print("❌ Failed to delete campaigns. Aborting.")
        sys.exit(1)
    
    print("━" * 80)
    print("🚀 Starting fresh scrape (10 campaigns per scraper)...")
    print("━" * 80)
    print()
    
    # Step 2: Define scrapers
    scrapers = [
        ("Garanti Bonus", "garantibonus.py"),
        ("Halkbank Paraf", "paraf.py"),
        ("Yapı Kredi World", "yapikredi_world.py"),
        ("Yapı Kredi Adios", "yapikredi_adios.py"),
        ("Yapı Kredi Play", "yapikredi_play.py"),
        ("Yapı Kredi Crystal", "yapikredi_crystal.py"),
    ]
    
    results = {
        'total': len(scrapers),
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    # Step 3: Run each scraper
    for i, (name, file) in enumerate(scrapers, 1):
        print("━" * 80)
        print(f"📦 [{i}/{results['total']}] Scraping: {name} (limit: 10)")
        print("━" * 80)
        
        success = run_scraper(name, file, limit=10)
        
        if success:
            results['success'] += 1
        else:
            results['failed'] += 1
            results['errors'].append(name)
        
        # Wait between scrapers
        if i < results['total']:
            print("\n⏳ Waiting 2 seconds before next scraper...\n")
            time.sleep(2)
    
    # Final summary
    print("\n" + "━" * 80)
    print("✅ FRESH SCRAPE COMPLETED!")
    print("━" * 80)
    print()
    print("📊 Summary:")
    print(f"   - Total scrapers: {results['total']}")
    print(f"   - Successful: {results['success']}")
    print(f"   - Failed: {results['failed']}")
    print(f"   - Expected campaigns: ~{results['success'] * 10}")
    print()
    
    if results['errors']:
        print("❌ Failed scrapers:")
        for error in results['errors']:
            print(f"   - {error}")
        print()
    
    print("🔍 Check results at: http://localhost:3000")
    print()

if __name__ == "__main__":
    main()
