
import os
from src.services.ai_parser import parse_api_campaign

# Read the temp file
with open('temp_axess.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Extract just the cmsContent part to simulate what the scraper does
from bs4 import BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')
detail_container = soup.select_one('.cmsContent.clearfix')
details_text = ""
if detail_container:
    # Remove scripts and styles
    for script in detail_container(["script", "style"]):
        script.decompose()
    details_text = detail_container.get_text(separator="\n", strip=True)

print("--- EXTRACTED TEXT ---")
print(details_text[:500] + "...")
print("----------------------")

# Call the parser
result = parse_api_campaign(
    title="Axess Giyim Alışverişlerinde 500 TL Chip-para Kazandırıyor!",
    short_description="Axess Giyim Alışverişlerinde 500 TL Chip-para Kazandırıyor!",
    content_html=details_text,
    bank_name="Akbank",
    scraper_sector=None
)

import json
print("\n--- AI PARSER RESULT ---")
print(json.dumps(result, indent=2, ensure_ascii=False))
