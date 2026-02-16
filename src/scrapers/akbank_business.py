
from .akbank_base import AkbankBaseScraper

class AkbankBusinessScraper(AkbankBaseScraper):
    """
    Scraper for Akbank Business (Ticari) campaigns.
    """
    def __init__(self):
        super().__init__(
            card_name="Axess Business",
            base_url="https://www.axess.com.tr",
            list_url="https://www.axess.com.tr/ajax/kampanya-ajax-ticari.aspx",
            referer_url="https://www.axess.com.tr/ticarikartlar/kampanya/8/450/kampanyalar",
            list_params={'checkBox': '[]', 'searchWord': '""'}
        )

if __name__ == "__main__":
    scraper = AkbankBusinessScraper()
    scraper.run()
