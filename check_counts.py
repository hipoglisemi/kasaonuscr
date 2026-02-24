import requests
import json
import urllib3
from bs4 import BeautifulSoup
import time
import re

urllib3.disable_warnings()

# Garanti headers from scraper
GARANTI_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
}

def check_ziraat():
    try:
        campaigns = set()
        listcount = 0
        page = 1
        
        # Read the first response
        r = requests.get("https://www.bankkart.com.tr/kampanyalar", headers=GARANTI_HEADERS, verify=False, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        initial_items = soup.select(".campaign-box")
        listcount = len(initial_items)
        for i in initial_items: campaigns.add(i.get('href'))
        
        while page < 10:
            url = f"https://www.bankkart.com.tr/App_Plugins/ZiraatBankkart/DesignBankkart/GetMoreCamp.aspx?id={listcount}&t=0"
            r = requests.post(url, headers=GARANTI_HEADERS, verify=False, timeout=10)
            if not r.text.strip(): break
            s = BeautifulSoup(r.text, 'html.parser')
            items = s.select(".campaign-box")
            if not items: break
            for i in items: campaigns.add(i.get('href'))
            listcount += len(items)
            page += 1
            
        print(f"✅ Ziraat Bankkart: Found ~{len(campaigns)} campaigns officially.")
    except Exception as e:
        print(f"❌ Ziraat Error: {e}")

def check_garanti_bonus():
    try:
        url = "https://www.bonus.com.tr/kampanyalar"
        r = requests.get(url, headers=GARANTI_HEADERS, verify=False, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Using exact logic from Garanti scraper
        campaign_links = set()
        for link in soup.find_all('a', class_='direct', href=True):
            href = link['href']
            if '/kampanyalar/' in href and len(href.split('/')) > 2:
                if not any(x in href for x in ['sektor', 'kategori', 'marka', '#', 'javascript']):
                    campaign_links.add(href)
                    
        print(f"✅ Garanti Bonus: Found {len(campaign_links)} kampanyalar officially on SSR load.")
    except Exception as e:
        print(f"❌ Garanti Error: {e}")

def check_halkbank_paraf():
    try:
        urls = [
            "https://www.paraf.com.tr/content/parafcard/tr/kampanyalar/_jcr_content/root/responsivegrid/filter.filtercampaigns.all.json",
            "https://www.parafly.com.tr/content/parafly/tr/kampanyalar/_jcr_content/root/responsivegrid/filter.filtercampaigns.all.json"
        ]
        total = 0
        for u in urls:
            r = requests.get(u, headers=GARANTI_HEADERS, verify=False, timeout=10)
            data = r.json()
            if isinstance(data, list):
                total += len(data)
            elif isinstance(data, dict):
                 total += len(data.get('campaigns', []))
        print(f"✅ Halkbank (Paraf+Parafly): Found {total} kampanyalar officially via API.")
    except Exception as e:
        print(f"❌ Halkbank Error: {e}")

def check_isbankasi():
    try:
        url = "https://www.maximum.com.tr/kampanyalar"
        r = requests.get(url, headers=GARANTI_HEADERS, verify=False, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        links = soup.find_all("a", href=True)
        camp_links = set([l['href'] for l in links if '/kampanyalar/' in l['href'] and 'arsiv' not in l['href'] and 'tum-kampanyalar' not in l['href']])
        
        text_content = r.text
        match = re.search(r'totalCount[\"\'\s:]+(\d+)', text_content)
        total = match.group(1) if match else "Unknown"
        
        print(f"✅ İş Bankası Maximum: Found {len(camp_links)} initially loaded. (JS Total claims: {total} kampanyalar)")
    except Exception as e:
        print(f"❌ İş Bankası Error: {e}")

if __name__ == "__main__":
    print("--- Official Website Campaign Counts ---")
    check_garanti_bonus()
    check_halkbank_paraf()
    check_isbankasi()
    check_ziraat()
