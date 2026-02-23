try:
    from .garanti_bonus import GarantiBonusScraper
except ImportError: GarantiBonusScraper = None

try:
    from .garanti_milesandsmiles import GarantiMilesAndSmilesScraper
except ImportError: GarantiMilesAndSmilesScraper = None

try:
    from .garanti_shopandfly import GarantiShopAndFlyScraper
except ImportError: GarantiShopAndFlyScraper = None

try:
    from .akbank_axess import AkbankAxessScraper
except ImportError: AkbankAxessScraper = None

try:
    from .akbank_free import AkbankFreeScraper
except ImportError: AkbankFreeScraper = None

try:
    from .akbank_business import AkbankBusinessScraper
except ImportError: AkbankBusinessScraper = None

try:
    from .isbankasi_maximum import IsbankMaximumScraper
except ImportError: IsbankMaximumScraper = None

try:
    from .enpara import EnparaScraper
except ImportError: EnparaScraper = None

__all__ = [
    'GarantiBonusScraper',
    'GarantiMilesAndSmilesScraper',
    'GarantiShopAndFlyScraper',
    'AkbankAxessScraper',
    'AkbankFreeScraper',
    'AkbankBusinessScraper',
    'IsbankMaximumScraper',
    'EnparaScraper'
]
