# --- 0. KURULUM (Google Colab / Linux Sunucu İçin) ---
import os
if not os.path.exists("/usr/bin/google-chrome"):
    print("Kurulum yapılıyor...")
    os.system("pip install selenium webdriver-manager requests beautifulsoup4")
    os.system("apt-get update")
    os.system("apt-get install -y google-chrome-stable")
    print("Kurulum tamamlandı.")

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import json
import re
from datetime import datetime
import random
import copy

# --- SELENIUM ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- 1. AYARLAR ---
BASE_URL = "https://www.bankkart.com.tr"
LIST_URL = "https://www.bankkart.com.tr/kampanyalar"
JSON_FILE_NAME = "ziraat_kampanyalar_v31_ultimate.json"
IMPORT_SOURCE_NAME = "Ziraat Bankkart"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# --- 2. YARDIMCI FONKSİYONLAR ---

def tr_lower(text):
    return text.replace('I', 'ı').replace('İ', 'i').lower()

def temizle_metin(text):
    if not text: return ""
    text = text.replace('\n', ' ').replace('\r', '')
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'^(Sektör:|Kampanya Koşulları:|Kampanya Detayları:)\s*', '', text, flags=re.IGNORECASE)
    text = text.strip(' ,.:;-')
    return text

def format_rakam(rakam_int):
    if rakam_int is None: return None
    try: return f"{int(rakam_int):,}".replace(",", ".")
    except: return None

def text_to_int_tr_max(text):
    text = tr_lower(text)
    mapping = {
        'birinci': 1, 'ilk': 1, 'ikinci': 2, 'üçüncü': 3, 'dördüncü': 4, 'beşinci': 5,
        'altıncı': 6, 'yedinci': 7, 'sekizinci': 8, 'dokuzuncu': 9, 'onuncu': 10
    }
    found_values = []
    for k, v in mapping.items():
        if k in text: found_values.append(v)
    matches_digit = re.findall(r'(\d+)\.\s*(?:işlem|harcama|alışveriş|akaryakıt)', text)
    if matches_digit:
        for m in matches_digit: found_values.append(int(m))
    return max(found_values) if found_values else None

def format_tarih_iso_v25(tarih_str, is_end_date=False):
    if not tarih_str: return None, None
    tarih_str = tr_lower(tarih_str)
    aylar = {'ocak': '01', 'şubat': '02', 'mart': '03', 'nisan': '04', 'mayıs': '05', 'haziran': '06',
             'temmuz': '07', 'ağustos': '08', 'eylül': '09', 'ekim': '10', 'kasım': '11', 'aralık': '12'}
    try:
        if "son gün" in tarih_str:
             match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', tarih_str)
             if match:
                 g, a, y = match.groups()
                 iso_str = f"{y}-{a.zfill(2)}-{g.zfill(2)}T23:59:59Z" if is_end_date else f"{y}-{a.zfill(2)}-{g.zfill(2)}T00:00:00Z"
                 return iso_str, datetime(int(y), int(a), int(g))
        parcalar = tarih_str.split()
        if len(parcalar) < 2: return None, None 
        gun_str = parcalar[0].zfill(2); ay_num = None
        for p in parcalar:
            if p in aylar: ay_num = aylar[p]; break
        if not ay_num: return None, None
        yil_str = str(datetime.now().year) 
        if parcalar[-1].isdigit() and len(parcalar[-1]) == 4: yil_str = parcalar[-1]
        tarih_obj = datetime(int(yil_str), int(ay_num), int(gun_str))
        iso_str = f"{yil_str}-{ay_num}-{gun_str}T23:59:59Z" if is_end_date else f"{yil_str}-{ay_num}-{gun_str}T00:00:00Z"
        return iso_str, tarih_obj 
    except: return None, None 

# --- KATEGORİ BELİRLEME (Gelişmiş) ---
def get_explicit_category_ziraat(content_div, full_text_search, title):
    """
    Sektör bilgisini HTML'den veya metinden çeker, E-Ticaret devlerini tanır.
    """
    # 1. Özel Marka Kontrolü (Hardcoded Fixes)
    title_lower = tr_lower(title)
    if any(x in title_lower for x in ["trendyol", "amazon", "hepsiburada", "n11", "pazarama", "e-ticaret"]):
        return "Online Alışveriş"

    raw_sector = ""
    # 2. HTML'den "Sektör:" etiketini bul
    if content_div:
        # "Sektör:" metnini içeren strong veya b etiketini bul
        # Ziraat'te genelde <p><strong>Sektör: </strong>Market...</p> şeklindedir
        sector_el = content_div.find('strong', string=re.compile(r'Sektör', re.IGNORECASE))
        if sector_el and sector_el.parent:
            raw_sector = sector_el.parent.get_text().replace('Sektör:', '').strip()
    
    # 3. Metin içinden Regex ile bul
    if not raw_sector:
        match = re.search(r'Sektör:\s*(.*?)(?:,|$|\.)', full_text_search, re.IGNORECASE)
        if match: raw_sector = match.group(1).strip()

    if not raw_sector: return None

    raw_lower = tr_lower(raw_sector)
    if "akaryakıt" in raw_lower: return "Yakıt"
    if "market" in raw_lower or "gıda" in raw_lower: return "Market"
    if "restoran" in raw_lower or "kafe" in raw_lower: return "Restoran & Kafe"
    if "giyim" in raw_lower or "aksesuar" in raw_lower: return "Giyim & Moda"
    if "elektronik" in raw_lower or "telekom" in raw_lower or "beyaz eşya" in raw_lower: return "Elektronik"
    if "mobilya" in raw_lower or "dekorasyon" in raw_lower: return "Ev & Yaşam"
    if "turizm" in raw_lower or "seyahat" in raw_lower or "konaklama" in raw_lower: return "Seyahat"
    if "e-ticaret" in raw_lower: return "Online Alışveriş"
    if "eğitim" in raw_lower or "kitap" in raw_lower or "kırtasiye" in raw_lower: return "Eğitim / Kırtasiye"
    if "sağlık" in raw_lower or "kozmetik" in raw_lower: return "Sağlık & Güzellik"
    if "yapı" in raw_lower: return "Market"
    
    return "Diğer"

def tahmin_et_kategori_fallback(text):
    text = tr_lower(text)
    if re.search(r'yakıt|akaryakıt|benzin|shell|opet|bp|lukoil|total', text): return 'Yakıt'
    if re.search(r'market|migros|carrefour|a101|şok|bim|gıda', text): return 'Market'
    if re.search(r'restoran|yemek|cafe|restaurant|burger|pizza|yemeksepeti', text): return 'Restoran & Kafe'
    if re.search(r'elektronik|teknoloji|mediamarkt|itopya|dyson|teknosa|vatan|monster', text): return 'Elektronik'
    if re.search(r'giyim|moda|ayakkabı|lcwaikiki|defacto|beymen|boyner|koton|mavi|network|divarese', text): return 'Giyim & Moda'
    if re.search(r'\bev\b|mobilya|dekorasyon|ikea|istikbal|bellona|karaca|schafer|yataş|işbir', text): return 'Ev & Yaşam'
    if re.search(r'trendyol|hepsiburada|amazon|n11|pazarama', text): return 'Online Alışveriş' 
    if re.search(r'seyahat|otel|tatil|uçak|turizm|bilet|touristica|coral|gezinomi|setur|jolly|ets', text): return 'Seyahat'
    if re.search(r'kozmetik|güzellik|bakım|gratis|watsons|rossmann', text): return 'Sağlık & Güzellik'
    return 'Diğer'

def extract_merchant_smart(title):
    if not title: return None
    try:
        match = re.search(r"(.+?)(?:'da|'de|'te|'ta|’da|’de|’te|’ta)\s+(?:peşin|taksit|\d|indirim|chip)", title, re.IGNORECASE)
        if match:
            candidate = temizle_metin(match.group(1))
            if "Axess" not in candidate and "Bankkart" not in candidate: return candidate
        match = re.search(r"(?:Axess|Bankkart)\s*(?:ile|'le|'la)\s+(.+?)(?:'da|'de|'te|'ta)", title, re.IGNORECASE)
        if match: return temizle_metin(match.group(1))
    except: pass
    return None

def extract_eligible_cards_advanced(text, title):
    eligible_cards = []
    text_lower = tr_lower(text + " " + title)
    if "genç" in text_lower: eligible_cards.append("Bankkart Genç")
    if "prestij" in text_lower: eligible_cards.append("Bankkart Prestij")
    if "başak" in text_lower: eligible_cards.append("Bankkart Başak")
    if "business" in text_lower or "kurumsal" in text_lower: eligible_cards.append("Bankkart Business")
    if "ücretsiz" in text_lower: eligible_cards.append("Bankkart Ücretsiz")
    if "troy" in text_lower: eligible_cards.append("TROY Logolu Bankkart")
    if "bireysel" in text_lower or not eligible_cards:
         if "Bireysel Bankkart" not in eligible_cards: eligible_cards.insert(0, "Bireysel Bankkart")
    
    sentences = text_lower.split('.')
    for sent in sentences:
        if "dahil değildir" in sent or "geçerli değildir" in sent or "kapsam dışıdır" in sent:
            if "başak" in sent and "Bankkart Başak" in eligible_cards: eligible_cards.remove("Bankkart Başak")
            if "business" in sent and "Bankkart Business" in eligible_cards: eligible_cards.remove("Bankkart Business")
            if "genç" in sent and "Bankkart Genç" in eligible_cards: eligible_cards.remove("Bankkart Genç")
            if "ücretsiz" in sent and "Bankkart Ücretsiz" in eligible_cards: eligible_cards.remove("Bankkart Ücretsiz")
            if "prestij" in sent and "Bankkart Prestij" in eligible_cards: eligible_cards.remove("Bankkart Prestij")
    if "Bankkart Prestij" in eligible_cards and "prestij plus" in text_lower:
        eligible_cards.append("Bankkart Prestij Plus")
    return sorted(list(set(eligible_cards)))

# --- V31 MATEMATİK MOTORU (Nokta Fix) ---
def extract_financials_v31(text, title):
    min_entry_limit = 0; max_discount = 0; discount_perc = 0; final_earning = None; final_discount = None
    calculated_total_spend = 0 
    is_pure_installment = False
    
    # 1. Rakam Temizliği (NOKTA FİX): "2.500" -> "2500"
    # Rakamların arasındaki noktayı sil, virgülü nokta yap (ondalık için)
    text_clean_nums = re.sub(r'(?<=\d)\.(?=\d)', '', text) 
    text_lower = tr_lower(text_clean_nums).replace(',', '.')
    title_lower = tr_lower(title)

    match_total = re.search(r'toplam(?:da)?\s*(\d+)\s*tl', text_lower)
    if match_total: max_discount = int(match_total.group(1))

    taksit_matches = re.findall(r'(\d+)\s*(?:taksit|aya varan)', text_lower)
    if taksit_matches:
        max_taksit = max([int(m) for m in taksit_matches])
        final_discount = f"{max_taksit} Taksit"
        match_simple = re.search(r'(\d+)\s*tl.*?taksit', text_lower)
        if match_simple: min_entry_limit = int(match_simple.group(1)); calculated_total_spend = min_entry_limit
        if not re.search(r'bankkart lira|indirim|puan|hediye|kazan', text_lower): is_pure_installment = True

    if ("taksit" in title_lower and "puan" not in title_lower and "indirim" not in title_lower) or is_pure_installment:
        return calculated_total_spend, None, final_discount, 0, 0

    match_perc = re.search(r'%\s*(\d+)', text_lower)
    if match_perc and not is_pure_installment:
        discount_perc = int(match_perc.group(1))
        suffix = "İndirim" if "indirim" in text_lower else "Bankkart Lira"
        match_spend = re.search(r'(\d+)\s*tl\s*(?:ve üzeri|üzeri)', text_lower)
        if match_spend: min_entry_limit = int(match_spend.group(1))
        if max_discount > 0:
            final_earning = f"{format_rakam(max_discount)} TL {suffix}"
            if discount_perc > 0: calculated_total_spend = int(max_discount * 100 / discount_perc)
        else:
            final_earning = f"%{discount_perc} {suffix}"
            calculated_total_spend = min_entry_limit
        return calculated_total_spend, final_earning, final_discount, discount_perc, max_discount

    matches_tiers = re.findall(r'(\d+)\s*tl\s*(?:ve üzeri|üzeri).*?(\d+)\s*tl', text_lower)
    if matches_tiers and not is_pure_installment:
        pairs = []
        for m in matches_tiers: pairs.append((int(m[0]), int(m[1])))
        if pairs:
            best_pair = max(pairs, key=lambda x: x[1])
            min_entry_limit = min(p[0] for p in pairs)
            max_discount = best_pair[1]
            suffix = "İndirim" if "indirim" in text_lower else "Bankkart Lira"
            
            match_total_cap = re.search(r'toplam(?:da)?\s*(\d+)\s*tl', text_lower)
            total_cap = int(match_total_cap.group(1)) if match_total_cap else 0
            
            if total_cap > max_discount and max_discount > 0:
                 count = total_cap / max_discount
                 calculated_total_spend = int(count * best_pair[0])
                 max_discount = total_cap
                 final_earning = f"{format_rakam(max_discount)} TL {suffix}"
            else:
                 calculated_total_spend = best_pair[0]
                 final_earning = f"{format_rakam(max_discount)} TL {suffix}"
            return calculated_total_spend, final_earning, final_discount, None, max_discount

    match_cumulative = re.search(r'toplam\s*(\d+)\s*tl.*?ulaşan', text_lower)
    if match_cumulative and not is_pure_installment:
        calculated_total_spend = int(match_cumulative.group(1))
        match_reward = re.search(r'(\d+)\s*tl\s*bankkart lira', text_lower)
        if match_reward:
             reward_val = int(match_reward.group(1))
             if not max_discount: max_discount = reward_val
             final_earning = f"{format_rakam(reward_val)} TL Bankkart Lira"
        return calculated_total_spend, final_earning, final_discount, None, max_discount

    max_step = text_to_int_tr_max(text_lower) or 0
    if max_step > 1 and not is_pure_installment:
        match_spend = re.search(r'(\d+)\s*tl\s*(?:ve üzeri|üzeri)', text_lower)
        spend_limit = int(match_spend.group(1)) if match_spend else 0
        match_reward = re.search(r'(\d+)\s*tl\s*bankkart lira', text_lower)
        reward_val = int(match_reward.group(1)) if match_reward else 0
        if spend_limit > 0:
            min_entry_limit = spend_limit; calculated_total_spend = spend_limit * max_step
        if reward_val > 0:
             final_earning = f"{format_rakam(reward_val)} TL Bankkart Lira"
             if not max_discount: max_discount = reward_val
        return calculated_total_spend, final_earning, final_discount, None, max_discount

    pattern_recurring = re.search(r'her\s*(\d+)\s*tl.*?(\d+)\s*tl', text_lower)
    if pattern_recurring and not is_pure_installment:
        spend_per_tx = int(pattern_recurring.group(1)); reward_per_tx = int(pattern_recurring.group(2))
        min_entry_limit = spend_per_tx
        if max_discount > 0:
            final_earning = f"{format_rakam(max_discount)} TL Bankkart Lira"
            if reward_per_tx > 0:
                count = max_discount / reward_per_tx
                calculated_total_spend = int(count * spend_per_tx)
        else:
            final_earning = f"{format_rakam(reward_per_tx)} TL Bankkart Lira"
            calculated_total_spend = spend_per_tx
        return calculated_total_spend, final_earning, final_discount, None, max_discount

    if min_entry_limit == 0:
        match_simple = re.search(r'(\d+)\s*tl\s*(?:ve üzeri|üzeri)', text_lower)
        if match_simple: 
            min_entry_limit = int(match_simple.group(1)); calculated_total_spend = min_entry_limit

    if not final_earning and not final_discount:
        match_reward = re.search(r'(\d+)\s*tl\s*(?:bankkart lira|indirim)', text_lower)
        if match_reward:
            val = int(match_reward.group(1))
            if val != min_entry_limit:
                suffix = "İndirim" if "indirim" in text_lower else "Bankkart Lira"
                final_earning = f"{format_rakam(val)} TL {suffix}"
                if not max_discount: max_discount = val
                if not calculated_total_spend and min_entry_limit > 0: calculated_total_spend = min_entry_limit

    if calculated_total_spend == 0 and min_entry_limit > 0:
        calculated_total_spend = min_entry_limit

    return calculated_total_spend, final_earning, final_discount, discount_perc, max_discount

def get_description_safe(content_div, title):
    if not content_div: return title
    div_clone = BeautifulSoup(str(content_div), 'html.parser')
    for unwanted in div_clone.select('.tabs-form, .share-box, .detail-info-box'): unwanted.decompose()
    text_all = div_clone.get_text(separator=' ')
    if "Kampanya Koşulları" in text_all:
        description = text_all.split("Kampanya Koşulları")[0]
    else:
        description = text_all
    description = temizle_metin(description)
    if len(description) > 400: description = description[:400].rsplit(' ', 1)[0] + "..."
    if len(description) < 10: 
        list_items = content_div.select('ul li')
        if list_items: description = temizle_metin(list_items[0].text)
        else: description = title
    return description

def extract_participation_ziraat(text):
    methods = []; category = "Kampanya detaylarını kontrol ediniz."
    text_lower = tr_lower(text)
    if "bankkart mobil" in text_lower: methods.append("Bankkart Mobil")
    if "bankkart.com.tr" in text_lower: methods.append("Web Sitesi")
    match_sms = re.search(r'["“]?([A-Z0-9]+)["”]?\s*yazıp\s*.*?(\d{4})', text, re.IGNORECASE)
    if match_sms: methods.append(f"SMS ({match_sms.group(1)} yazıp {match_sms.group(2)}'e)")
    if "otomatik" in text_lower: category = "Otomatik Katılım"; methods = ["Otomatik katılım"]
    if methods: methods = list(set(methods)); category = ", ".join(methods)
    return category, methods

def clean_conditions_ziraat(text_list):
    cleaned = []
    for line in text_list:
        line = temizle_metin(line)
        if not line: continue
        if "T.C. Ziraat Bankası A.Ş." in line: continue
        cleaned.append(line)
    return cleaned

# --- 3. ANA İŞLEM ---
def get_campaign_list_selenium_scroll():
    print("Aşama 1: Selenium ile tüm liste toplanıyor (Sonsuz Kaydırma)...")
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox") 
    chrome_options.add_argument("--disable-dev-shm-usage") 
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    if os.path.exists("/usr/bin/google-chrome"): chrome_options.binary_location = "/usr/bin/google-chrome"
    driver = None
    campaign_urls = []
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(LIST_URL)
        time.sleep(3)
        last_height = driver.execute_script("return document.body.scrollHeight")
        no_change_count = 0
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2.5)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                no_change_count += 1
                if no_change_count >= 3: break
            else:
                no_change_count = 0
                last_height = new_height
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        cards = soup.select('a.campaign-box')
        for card in cards:
            link = card.get('href')
            if link:
                full_url = urljoin(BASE_URL, link)
                if full_url not in campaign_urls: campaign_urls.append(full_url)
        print(f"   -> Toplam {len(campaign_urls)} kampanya bulundu.")
    except Exception as e: print(f"Selenium Hatası: {e}")
    finally:
        if driver: driver.quit()
    return campaign_urls

def get_campaign_details_ziraat(session, url, campaign_id):
    print(f"Detaylar (ID: {campaign_id}): {url.split('/')[-1][:35]}...")
    try:
        response = session.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
    except: return None

    title = ""
    title_candidates = [soup.select_one('h1'), soup.select_one('.page-title'), soup.select_one('.subpage-detail h1')]
    for c in title_candidates:
        if c and len(temizle_metin(c.text)) > 5: title = temizle_metin(c.text); break
    if not title: title = "Başlık Bulunamadı"

    image_el = soup.select_one('#firstImg') or soup.select_one('.subpage-detail figure img')
    image_url = urljoin(BASE_URL, image_el['src']) if image_el else None

    valid_from_iso, valid_until_iso = None, None
    try:
        date_box = soup.select_one('.date-box h4')
        if date_box:
            date_text = temizle_metin(date_box.text)
            match_range = re.search(r'(.*?)\s*-\s*(.*)', date_text)
            if match_range:
                s, e = match_range.groups()
                if not re.search(r'\d{4}', s) and re.search(r'\d{4}', e): y = re.search(r'\d{4}', e).group(0); s += f" {y}"
                valid_from_iso, _ = format_tarih_iso_v25(s, False)
                valid_until_iso, _ = format_tarih_iso_v25(e, True)
    except: pass

    content_div = soup.select_one('.detail-content')
    full_text = ""; description = ""; conditions_list = []
    if content_div:
        list_items = content_div.select('ul li')
        raw_conditions = [li.get_text() for li in list_items]
        conditions_list = clean_conditions_ziraat(raw_conditions)
        description = get_description_safe(content_div, title)
        
        clone_div = BeautifulSoup(str(content_div), 'html.parser')
        for u in clone_div.select('.tabs-form, .share-box, .detail-info-box'): u.decompose()
        # FULL TEXT İÇİNDE LİSTELER DE OLSUN (MATEMATİK İÇİN)
        full_text = temizle_metin(clone_div.get_text(separator=' '))
    
    # KATEGORİ BELİRLEME (HTML'den oku, yoksa tahmin et)
    category = get_explicit_category_ziraat(content_div, full_text, title)
    if not category or category == "Diğer":
         category = tahmin_et_kategori_fallback(title + " " + full_text)

    merchant = extract_merchant_smart(title)
    
    min_spend, earning, discount_str, disc_perc, max_disc = extract_financials_v31(description + " " + full_text, title)
    
    if max_disc > 0 and earning and "Taksit" not in str(discount_str):
        try:
            curr_val = int(re.sub(r'\D', '', earning.split()[0]))
            if curr_val < max_disc:
                 suffix = "İndirim" if "İndirim" in earning else "Bankkart Lira"
                 earning = f"{format_rakam(max_disc)} TL {suffix}"
        except: pass

    part_method, part_points = extract_participation_ziraat(full_text)
    difficulty = "Kolay" if "Otomatik" in part_method else ("Orta" if "SMS" in part_method else "Orta")
    eligible_customers = extract_eligible_cards_advanced(full_text, title)

    return {
        "id": campaign_id, "title": title, "provider": IMPORT_SOURCE_NAME,
        "category": category, "merchant": merchant,
        "image": image_url, "images": [image_url] if image_url else [],
        "featured": False, "description": description, "url": url, "views": 0,
        "discount": discount_str, "earning": earning,
        "min_spend": min_spend, "max_discount": max_disc,
        "discount_percentage": disc_perc,
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "valid_from": valid_from_iso, "valid_until": valid_until_iso,
        "votes_up": 0, "votes_down": 0,
        "participation_method": part_method, "participation_points": part_points,
        "conditions": conditions_list, "eligible_customers": eligible_customers,
        "valid_locations": None, "difficulty_level": difficulty, "source_url": BASE_URL
    }

if __name__ == "__main__":
    print(f"{IMPORT_SOURCE_NAME} Scraper (v31 - Ultimate) Başlıyor...")
    all_urls = get_campaign_list_selenium_scroll()
    all_data = []
    if all_urls:
        print(f"\n--- {len(all_urls)} Kampanya detaylandırılıyor ---\n")
        with requests.Session() as session:
            for i, url in enumerate(all_urls, 1):
                data = get_campaign_details_ziraat(session, url, i)
                if data: all_data.append(data)
        try:
            with open(JSON_FILE_NAME, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=4)
            print(f"\n🎉 BAŞARILI! {len(all_data)} kampanya kaydedildi: {JSON_FILE_NAME}")
        except Exception as e: print(f"Kayıt Hatası: {e}")