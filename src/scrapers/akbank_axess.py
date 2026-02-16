
from .akbank_base import AkbankBaseScraper

class AkbankAxessScraper(AkbankBaseScraper):
    """
    Scraper for Akbank Axess campaigns.
    """
    def __init__(self):
        super().__init__(
            card_name="Axess",
            base_url="https://www.axess.com.tr",
            list_url="https://www.axess.com.tr/ajax/kampanya-ajax.aspx",
            referer_url="https://www.axess.com.tr/kampanyalar",
            list_params={'checkBox': '[0]', 'searchWord': '""'}
        )

if __name__ == "__main__":
    scraper = AkbankAxessScraper()
    scraper.run()
