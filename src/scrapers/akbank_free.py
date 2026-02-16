
from .akbank_base import AkbankBaseScraper

class AkbankFreeScraper(AkbankBaseScraper):
    """
    Scraper for Akbank Free Card campaigns.
    """
    def __init__(self):
        super().__init__(
            card_name="Axess Free",
            base_url="https://www.kartfree.com",
            list_url="https://www.kartfree.com/ajax/kampanya-ajax-free.aspx",
            referer_url="https://www.kartfree.com/kampanyalar",
            list_params={'checkBox': '[]', 'searchWord': '""'}
        )

if __name__ == "__main__":
    scraper = AkbankFreeScraper()
    scraper.run()
