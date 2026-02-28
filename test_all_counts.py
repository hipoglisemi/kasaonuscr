import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.scrapers.akbank_axess import AkbankAxessScraper
from src.scrapers.akbank_business import AkbankBusinessScraper
from src.scrapers.akbank_free import AkbankFreeScraper
from src.scrapers.akbank_wings import AkbankWingsScraper
from src.scrapers.chippin import ChippinScraper
from src.scrapers.denizbank import DenizbankScraper
from src.scrapers.garanti_bonus import GarantiBonusScraper
from src.scrapers.garanti_milesandsmiles import GarantiMilesAndSmilesScraper
from src.scrapers.garanti_shopandfly import GarantiShopAndFlyScraper
from src.scrapers.isbankasi_genc import IsbankMaximumGencScraper
from src.scrapers.isbankasi_maximiles import IsbankMaximilesScraper
from src.scrapers.paraf_genc import ParafGencScraper
from src.scrapers.qnb import QNBScraper
from src.scrapers.teb import TEBScraper
from src.scrapers.turkiyefinans import TurkiyeFinansScraper
from src.scrapers.yapikredi_adios import YapikrediAdiosScraper
from src.scrapers.yapikredi_crystal import YapikrediCrystalScraper
from src.scrapers.yapikredi_play import YapikrediPlayScraper
from src.scrapers.yapikredi_world import YapikrediWorldScraper
from src.scrapers.ziraat import ZiraatScraper

def try_get_links(name, scraper_obj, method_name):
    try:
        # Check if selenium driver needed
        if hasattr(scraper_obj, '_get_driver') and getattr(scraper_obj, 'driver', None) is None:
            scraper_obj.driver = scraper_obj._get_driver()
            
        links = getattr(scraper_obj, method_name)()
        if isinstance(links, list):
            print(f"- **{name}:** {len(links)} kampanya buldu.")
        elif isinstance(links, dict) or isinstance(links, set):
            print(f"- **{name}:** {len(links)} kampanya buldu.")
        else:
            print(f"- **{name}:** Bulunamadı veya format farklı.")
            
        # Clean up
        if hasattr(scraper_obj, 'driver') and scraper_obj.driver:
            scraper_obj.driver.quit()
        if hasattr(scraper_obj, 'display') and scraper_obj.display:
            scraper_obj.display.stop()
            
    except Exception as e:
        print(f"- **{name}:** Hata! {e}")

def main():
    print("### 4. Akbank Scrapers")
    try_get_links("Akbank Axess", AkbankAxessScraper(), "_fetch_campaign_list")
    try_get_links("Akbank Business", AkbankBusinessScraper(), "_fetch_campaign_list")
    try_get_links("Akbank Free", AkbankFreeScraper(), "_fetch_campaign_list")
    try_get_links("Akbank Wings", AkbankWingsScraper(), "_fetch_campaigns") # Assuming wings has list method

    print("\n### 5. Garanti Scrapers")
    from src.scrapers.garanti_bonus import GarantiBonusScraper
    try:
        g = GarantiBonusScraper()
        links = g._fetch_campaign_urls()
        print(f"- **Garanti Bonus:** {len(links)} kampanya buldu.")
        if g.driver: g.driver.quit()
    except Exception as e: print("- **Garanti Bonus:** Hata!", e)
    
    try_get_links("Garanti Miles&Smiles", GarantiMilesAndSmilesScraper(), "_fetch_campaign_list")
    try_get_links("Garanti Shop&Fly", GarantiShopAndFlyScraper(), "_fetch_campaign_list")

    print("\n### 6. İş Bankası Scrapers")
    # try_get_links("İş Bankası Genç", IsbankMaximumGencScraper(), "_fetch_campaign_urls") # Takes long headless
    # try_get_links("İş Bankası Maximiles", IsbankMaximilesScraper(), "_fetch_campaign_urls")

    print("\n### 7. Yapı Kredi Scrapers")
    try_get_links("YK Adios", YapikrediAdiosScraper(), "_fetch_campaign_list")
    try_get_links("YK Crystal", YapikrediCrystalScraper(), "_fetch_campaign_list")
    try_get_links("YK Play", YapikrediPlayScraper(), "_fetch_campaign_list")
    try_get_links("YK World", YapikrediWorldScraper(), "_fetch_campaign_list")

    print("\n### 8. Diğer Bankalar")
    try_get_links("QNB", QNBScraper(), "_fetch_campaign_list")
    try_get_links("TEB", TEBScraper(), "_fetch_campaign_urls")
    try_get_links("Türkiye Finans", TurkiyeFinansScraper(), "_fetch_campaign_urls")
    try_get_links("Ziraat", ZiraatScraper(), "_fetch_campaign_list")
    try_get_links("Chippin", ChippinScraper(), "_fetch_campaign_list")

if __name__ == '__main__':
    main()
