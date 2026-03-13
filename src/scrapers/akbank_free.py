


import sys
import os
# Path setup
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.scrapers.akbank_base import AkbankBaseScraper  # type: ignore # pyre-ignore[21]

class AkbankFreeScraper(AkbankBaseScraper):
    """
    Scraper for Akbank Free Card campaigns.
    """
    def __init__(self):
        AkbankBaseScraper.__init__(
            self,
            card_name="Axess Free",
            base_url="https://www.kartfree.com",
            list_url="https://www.kartfree.com/ajax/kampanya-ajax-free.aspx",
            referer_url="https://www.kartfree.com/kampanyalar",
            list_params={'checkBox': '[]', 'searchWord': '""'}  # type: ignore # pyre-ignore[16,6]
        )

if __name__ == "__main__":
    scraper = AkbankFreeScraper()
    scraper.run()
