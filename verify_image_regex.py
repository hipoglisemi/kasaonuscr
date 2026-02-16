
import re

def test_extraction():
    # Sample HTML snippet from Paraf (simulated)
    style_attr = "background-image: url('/content/dam/parafcard/campaigns/2024/market-kampanya-banner.jpg')"
    
    print(f"Testing style attribute: {style_attr}")
    
    # Regex from src/scrapers/paraf.py
    # match = bannerDiv.style.backgroundImage.match(/url\(['"]?(.*?)['"]?\)/);
    
    # Python equivalent regex
    match = re.search(r"url\(['\"]?(.*?)['\"]?\)", style_attr)
    
    if match:
        extracted = match.group(1)
        print(f"✅ Extracted: {extracted}")
        
        # Logic to prepend base URL
        base_url = "https://www.paraf.com.tr"
        if extracted.startswith('/'):
            final_url = base_url + extracted
            print(f"✅ Final URL: {final_url}")
            return final_url
    else:
        print("❌ No match found")
        return None

if __name__ == "__main__":
    test_extraction()
