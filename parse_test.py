from src.database import get_db_session
from src.services.ai_parser import AIParser
from bs4 import BeautifulSoup
import requests

url = "https://dunyakatilim.com.tr/kampanyalar/ramazan-troy-kampanyasi"
r = requests.get(url, verify=False)
soup = BeautifulSoup(r.text, 'html.parser')
content_div = (
    soup.select_one('.news-campaign-content') or 
    soup.select_one('.bt') or 
    soup.select_one('.richtext') or 
    soup.find('h2', string=lambda text: text and 'Kampanya Koşulları' in text)
)

if content_div:
    if content_div.name == 'h2':
        raw_text = content_div.parent.get_text(separator='\n', strip=True) 
    else:
        raw_text = content_div.get_text(separator='\n', strip=True)
else:
    raw_text = soup.body.get_text(separator='\n', strip=True) if soup.body else ""

parser = AIParser()
ai_data = parser.parse_campaign_data(
    raw_text=raw_text,
    title="Ramazan Bereketi TROY’la geliyor!",
    bank_name="dunyakatilim",
    card_name="Dünya Katılım Kartı"
)
print("PARTICIPATION:", ai_data.get('participation'))
