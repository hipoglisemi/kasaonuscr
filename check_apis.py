import requests
from bs4 import BeautifulSoup

# List of scrapers and their base URLs
scrapers = {
    "Garanti Bonus": "https://www.bonus.com.tr/kampanyalar",
    "Garanti Miles&Smiles": "https://milesandsmilesgarantibbva.com",
    "Garanti Shop&Fly": "https://www.shopandfly.com.tr",
    "Yapı Kredi World": "https://www.worldcard.com.tr/kampanyalar",
    "Yapı Kredi Play": "https://www.yapikrediplay.com.tr/kampanyalar",
    "Yapı Kredi Crystal": "https://www.crystalcard.com.tr/kampanyalar",
    "Yapı Kredi Adios": "https://www.adioscard.com.tr/kampanyalar",
    "İş Bankası Maximum": "https://www.maximum.com.tr/kampanyalar",
    "İş Bankası MaxiMiles": "https://www.maximiles.com.tr/kampanyalar",
    "İş Bankası Genç": "https://www.maximumgenc.com.tr/kampanyalar",
    "VakıfBank": "https://www.vakifkart.com.tr/kampanyalar",
    "Ziraat Bankkart": "https://www.bankkart.com.tr/kampanyalar",
    "Akbank Wings": "https://www.wingscard.com.tr/kampanyalar"
}

print("🔍 Checking for JSON APIs...\n")

for name, url in scrapers.items():
    try:
        # Try to fetch the page
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Check if response is JSON
        content_type = response.headers.get('Content-Type', '')
        
        # Check for common API patterns in URL or response
        has_api_pattern = any(x in url.lower() for x in ['api', 'json', 'ajax'])
        is_json = 'application/json' in content_type
        
        # Try to parse as JSON
        try:
            data = response.json()
            print(f"✅ {name}: JSON API FOUND!")
            print(f"   URL: {url}")
            print(f"   Keys: {list(data.keys())[:5]}")
            print()
        except:
            # Check HTML for API calls
            soup = BeautifulSoup(response.text, 'html.parser')
            scripts = soup.find_all('script')
            
            api_urls = []
            for script in scripts:
                text = script.string or ''
                # Look for common API patterns
                if 'fetch(' in text or 'axios' in text or '.json' in text:
                    # Extract potential API URLs
                    import re
                    urls = re.findall(r'["\']([^"\']*(?:api|json|ajax)[^"\']*)["\']', text)
                    api_urls.extend(urls)
            
            if api_urls:
                print(f"⚠️  {name}: Potential API calls found in JavaScript")
                print(f"   Sample URLs: {api_urls[:3]}")
                print()
            else:
                print(f"❌ {name}: No JSON API detected (HTML scraping)")
                
    except Exception as e:
        print(f"❌ {name}: Error - {str(e)[:50]}")
    
print("\n✅ API check complete!")
