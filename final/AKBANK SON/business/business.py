import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import json
import os
import re
from datetime import datetime
import random

# --- 1. AYARLAR (Business v1) ---
BASE_URL = "https://www.axess.com.tr"
API_LIST_URL = "https://www.axess.com.tr/ajax/kampanya-ajax-ticari.aspx" # <--- SENİN BULDUĞUN
REFERER_URL = "https://www.axess.com.tr/ticarikartlar/kampanya/8/450/kampanyalar" # <--- SENİN BULDUĞUN
JSON_FILE_NAME = "axess_business_v1.json" # <--- ÇIKTI DOSYASI
IMPORT_SOURCE_NAME = "Axess Business (Ticari)" # <--- SAĞLAYICI ADI

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': REFERER_URL
}

# --- Seçiciler (HTML yapısı Axess ile aynı) ---
LIST_ITEM_SELECTOR = ".campaingBox a.dLink"
DETAIL_CONTAINER_SELECTOR = ".cmsContent.clearfix"
TITLE_SELECTOR = "h2.pageTitle"
IMAGE_SELECTOR = ".campaingDetailImage img"
IMAGE_BASE_URL = "https://www.axess.com.tr" # Resimler için ana kaynak


# --- 2. YARDIMCI FONKSİYONLAR (v28 - En Akıllı) ---
# (Tüm 'v28' mantığı buradadır)

def temizle_metin(text):
    if text: return re.sub(r'\s+', ' ', text).strip()
    return ""
def format_rakam(rakam_int):
    if rakam_int is None: return None
    try: return f"{int(rakam_int):,}".replace(",", ".")
    except (ValueError, TypeError): return None
def format_tarih_iso_v25(tarih_str, is_end_date=False):
    if not tarih_str: return None, None
    tarih_str = re.sub(r"['’`´](?:e|a|ye|ya|'de|'da|’de|’da)", "", tarih_str.lower().strip())
    aylar = {'ocak': '01', 'şubat': '02', 'mart': '03', 'nisan': '04', 'mayıs': '05', 'haziran': '06',
             'temmuz': '07', 'ağustos': '08', 'eylül': '09', 'ekim': '10', 'kasım': '11', 'aralık': '12'}
    try:
        parcalar = tarih_str.split();
        if len(parcalar) < 2: return None, None 
        gun_str = parcalar[0].zfill(2); ay_adi = parcalar[1]; ay_num = aylar.get(ay_adi);
        if not ay_num: return None, None
        yil_str = str(datetime.now().year) 
        if len(parcalar) > 2 and parcalar[2].isdigit() and len(parcalar[2]) == 4: yil_str = parcalar[2]
        tarih_obj = datetime(int(yil_str), int(ay_num), int(gun_str))
        if is_end_date: iso_str = f"{yil_str}-{ay_num}-{gun_str}T23:59:59Z"
        else: iso_str = f"{yil_str}-{ay_num}-{gun_str}T00:00:00Z"
        return iso_str, tarih_obj 
    except Exception: return None, None 
def tahmin_et_kategori_v25(text):
    text = text.lower()
    if re.search(r'yakıt|akaryakıt|benzin|shell|opet|bp', text): return 'Yakıt'
    if re.search(r'market|migros|carrefour|a101|şok|bim|gıda', text): return 'Market'
    if re.search(r'restoran|yemek|cafe|restaurant|burger|pizza|yemeksepeti', text): return 'Restoran & Kafe'
    if re.search(r'elektronik|teknoloji|mediamarkt|itopya|dyson|teknosa|gürgençler|monster|vestel', text): return 'Elektronik'
    if re.search(r'giyim|moda|ayakkabı|lcwaikiki|defacto|beymen|ipekyol|twist|koton|flo|columbia|desa|lacoste|ecrou|reebok|lumberjack|nine west|in street|polaris|zsa zsa zsu', text): return 'Giyim & Moda'
    if re.search(r'\bev\b|mobilya|dekorasyon|ikea|istikbal|bellona|işbir yatak|koçtaş|karaca|schafer|evidea|özdilek|idas|ider|korkmaz|vivense|alfemo', text): return 'Ev & Yaşam'
    if re.search(r'trendyol|hepsiburada|amazon|online|e-ticaret|n11|pazarama', text): return 'Online Alışveriş' 
    if re.search(r'seyahat|otel|tatil|uçak|turizm|duty.free|mil|puan|bilet|tatilsepeti|obilet|setur|touristica|enuygun', text): return 'Seyahat'
    if re.search(r'sinema|tiyatro|konser|eğlence|biletix|passo|theatreclix', text): return 'Eğlence'
    if re.search(r'kozmetik|güzellik|bakım|eczane|sağlık|watsons|gratis', text): return 'Sağlık & Güzellik'
    if re.search(r'spor|outdoor|decathlon|adidas|nike|puma', text): return 'Spor & Outdoor'
    if re.search(r'kitap|kırtasiye|dr|idefix|nezih', text): return 'Kitap & Kırtasiye'
    return 'Diğer'
def extract_dates_from_text_v25(text):
    valid_from, valid_until = None, None; text = temizle_metin(text)
    try:
        match = re.search(r'(\d{1,2}\s+[\wıöüçğş]+(?:\s+\d{4})?)\s*(?:-|–)\s*(\d{1,2}\s+[\wıöüçğş]+\s+\d{4})', text, re.IGNORECASE)
        if match:
            valid_from = temizle_metin(match.group(1)); valid_until = temizle_metin(match.group(2))
            year_match = re.search(r'(\d{4})', valid_until);
            if year_match and not re.search(r'\d{4}', valid_from): valid_from += " " + year_match.group(1)
            return valid_from, valid_until
        match = re.search(r'(\d{1,2}\s+[\wıöüçğş]+)\s*(?:-|–)\s*(\d{1,2}\s+[\wıöüçğş]+(\s+\d{4}))', text, re.IGNORECASE)
        if match:
            valid_from = temizle_metin(match.group(1)); valid_until = temizle_metin(match.group(2))
            year_match = re.search(r'(\d{4})', valid_until);
            if year_match and not re.search(r'\d{4}', valid_from): valid_from += " " + year_match.group(1)
            return valid_from, valid_until
        match = re.search(r'(\d{1,2})\s*(?:-|–)\s*(\d{1,2}\s+([\wıöüçğş]+)((?:\s+\d{4})?))', text, re.IGNORECASE)
        if match:
            gun_baslangic = temizle_metin(match.group(1)); tam_bitis = temizle_metin(match.group(2)); ay = temizle_metin(match.group(3)) 
            yil_search = re.search(r'(\d{4})', tam_bitis); yil = yil_search.group(1) if yil_search else "" 
            valid_from = f"{gun_baslangic} {ay} {yil}"; valid_until = tam_bitis
            return valid_from, valid_until
        match = re.search(r"(\d{1,2}\s+[\wıöüçğş]+(?:\s+\d{4})?)\s*['’`´]?(?:ye|ya|e|a)?\s*kadar", text, re.IGNORECASE)
        if match:
            valid_until = temizle_metin(match.group(1)); return None, valid_until
    except Exception: pass 
    return None, None
def extract_financials_v27(text):
    min_spend_int, max_discount_int, discount_perc_int = None, None, None; final_earning, final_discount = None, None
    finance_text = text.lower(); taksit_str, chip_para_str, indirim_str = None, None, None
    all_chip_para_vals = []
    pattern_chip_para = re.findall(r'(\d+[\d.,]*)\s*(?:tl|₺)\s*(?:chip-para|hediye|iade)', finance_text, re.IGNORECASE)
    if not pattern_chip_para: pattern_chip_para = re.findall(r'(\d+[\d.,]*)\s*(?:tl|₺).{0,15}?(?:chip-para|hediye|iade|değerinde)', finance_text, re.IGNORECASE)
    for match in pattern_chip_para:
        val_str = match[0] if isinstance(match, tuple) else match
        try: all_chip_para_vals.append(int(val_str.replace('.','').replace(',','')))
        except (ValueError, IndexError): pass
    if all_chip_para_vals: best_chip_para_val = max(all_chip_para_vals); chip_para_str = f"{format_rakam(best_chip_para_val)} TL chip-para"
    taksit_numbers = []
    match_taksit = re.findall(r'(?<!ticari\s)(?<!azami\s)(?<!en fazla\s)(\d+)\s*(?:aya varan|ay)?\s*taksit', finance_text, re.IGNORECASE)
    if not match_taksit: match_taksit = re.findall(r'vade farksız\s*(\d+)', finance_text, re.IGNORECASE)
    if not match_taksit: match_taksit = re.findall(r'(\d+)\s*(?:aya varan|ay)?\s*taksit', finance_text, re.IGNORECASE)
    if match_taksit: taksit_numbers.extend(map(int, match_taksit))
    if taksit_numbers: taksit_str = f"{max(taksit_numbers)} Taksit"
    match_percent = re.search(r'%\s*(\d+)\s*indirim', finance_text, re.IGNORECASE)
    if match_percent: discount_perc_int = int(match_percent.group(1)); indirim_str = f"%{discount_perc_int} İndirim"
    match_tl_indirim = re.findall(r'(\d+[\d.,]*)\s*tl\s*indirim', finance_text, re.IGNORECASE)
    if match_tl_indirim and not indirim_str:
        tl_indirim_vals = [int(m.replace('.','').replace(',','')) for m in match_tl_indirim];
        if tl_indirim_vals: indirim_str = f"{format_rakam(max(tl_indirim_vals))} TL İndirim"
    if chip_para_str: final_earning = chip_para_str
    elif indirim_str: final_earning = indirim_str
    if taksit_str: final_discount = taksit_str
    max_earning_match = re.search(r"(?:toplamda|en fazla|maksimum)\s*(\d+[\d.,]*)\s*(?:tl|₺)", finance_text)
    if max_earning_match: max_discount_int = int(max_earning_match.group(1).replace('.','').replace(',',''))
    elif chip_para_str:
         try: max_discount_int = int(re.search(r"([\d\.]+)", chip_para_str.replace('.','')).group(1))
         except Exception: pass
    elif indirim_str and "TL" in indirim_str:
         try: max_discount_int = int(re.search(r"([\d\.]+)", indirim_str.replace('.','')).group(1))
         except Exception: pass
    spend_calculated = False
    try:
        pattern_repeating = re.search(r'her\s*([\d\.,]+)\s*(?:tl|₺).+?([\d\.,]+)\s*(?:tl|₺).+?(?:toplamda|toplam)\s*([\d\.,]+)\s*(?:tl|₺)', finance_text, re.IGNORECASE)
        if pattern_repeating:
            spend_per_tx_str, earn_per_tx_str, total_earn_str = pattern_repeating.groups()
            current_max_discount = int(total_earn_str.replace('.','').replace(',',''))
            if not max_discount_int: max_discount_int = current_max_discount
            spend_per_tx = int(spend_per_tx_str.replace('.','').replace(',',''))
            earn_per_tx = int(earn_per_tx_str.replace('.','').replace(',',''))
            if earn_per_tx > 0 and max_discount_int:
                num_tx = max_discount_int / earn_per_tx; min_spend_int = int(spend_per_tx * num_tx); spend_calculated = True
    except Exception: spend_calculated = False 
    if not spend_calculated:
        try:
            pattern_stepped = re.search(r'(\d+[\d.,]*)\s*(?:tl|₺)\s*(?:ve üzeri|üzeri).{0,25}?(\d+)\.\s*(?:akaryakıt|harcama|alışveriş)', finance_text, re.IGNORECASE)
            if pattern_stepped:
                spend_per_tx_str, num_tx_str = pattern_stepped.groups()
                spend_per_tx = int(spend_per_tx_str.replace('.','').replace(',','')); num_tx = int(num_tx_str)
                if num_tx > 0 and spend_per_tx > 0: min_spend_int = spend_per_tx * num_tx; spend_calculated = True
        except Exception: pass 
    if not spend_calculated:
        try:
            all_spends_int = []
            pattern_ranges = re.findall(r'(\d+[\d.,]*)\s*(?:tl|₺)\s*-\s*(\d+[\d.,]*)\s*(?:tl|₺)\s*arası', finance_text, re.IGNORECASE)
            if pattern_ranges:
                for spend_range in pattern_ranges: all_spends_int.append(int(spend_range[0].replace('.','').replace(',','')))
            if all_spends_int: min_spend_int = min(all_spends_int); spend_calculated = True
        except Exception: pass
    if not spend_calculated:
        try:
            all_spends_int = []
            pattern_spends = re.findall(r'(\d+[\d.,]*)\s*(?:tl|₺)\s*(?:ve üzeri|üzeri|harcama)', finance_text, re.IGNORECASE)
            if pattern_spends:
                for spend_str in pattern_spends: all_spends_int.append(int(spend_str.replace('.','').replace(',','')))
            if all_spends_int: min_spend_int = max(all_spends_int)
        except Exception: pass 
    return min_spend_int, final_earning, final_discount, discount_perc_int, max_discount_int
def extract_participation_v28(text, title):
    part_points_list = []; method_category = "Kampanya detaylarını kontrol ediniz.";
    found_app = False; found_sms = False
    if "fatura talimat" in title.lower():
        try:
            sms_match = re.search(r'["“]?\s*([A-Z0-9İÖÜŞĞÇ]+)\s*["”]?\s*yazıp\s*.*?(\d{4})', text, re.IGNORECASE)
            kanallar = []
            if re.search(r'Juzdan', text, re.IGNORECASE): kanallar.append("Juzdan")
            if re.search(r'Akbank Mobil', text, re.IGNORECASE): kanallar.append("Akbank Mobil")
            if re.search(r'Akbank İnternet', text, re.IGNORECASE): kanallar.append("Akbank İnternet")
            if re.search(r'444 25 25', text): kanallar.append("444 2525")
            if re.search(r'şubelerimizden', text, re.IGNORECASE): kanallar.append("Şubelerden")
            if sms_match or kanallar:
                short_text_parts = []
                if sms_match: sms_kod = sms_match.group(1); sms_num = sms_match.group(2); short_text_parts.append(f"{sms_kod} yazıp {sms_num}’a SMS")
                kanallar_str = ", ".join(kanallar)
                if kanallar_str: short_text_parts.append(kanallar_str)
                short_text = ", ".join(short_text_parts); part_points_list = [short_text]; method_category = short_text
                return method_category, part_points_list
        except Exception: pass 
    match_app_text = ""; match_sms_text = ""
    match_app = re.search(r'((Juzdan|Akbank\s*Mobil).*?(?:“Hemen Katıl”|butonuna|üzerinden|sayfasındaki).*?tıkla\w*)', text, re.IGNORECASE)
    if match_app:
        match_app_text = temizle_metin(match_app.group(1)); part_points_list.append(match_app_text); method_category = "Uygulama üzerinden"; found_app = True
    match_sms = re.search(r'["“]?\s*([A-Z0-9İÖÜŞĞÇ]+)\s*["”]?\s*yazıp\s*.*?(\d{4})\s*\'?(?:e|ye|a)', text, re.IGNORECASE)
    if match_sms:
        match_sms_text = temizle_metin(match_sms.group(0)); part_points_list.append(match_sms_text); found_sms = True
    if found_app and found_sms: method_category = "SMS ve Uygulama"
    elif found_sms and not found_app: method_category = "SMS ile katılım"
    match_auto = re.search(r'(otomatik katılım|herhangi bir işlem gerekmez|otomatik olarak katıl)', text, re.IGNORECASE)
    if match_auto and not found_app and not found_sms:
        part_points_list.append(temizle_metin(match_auto.group(0))); method_category = "Otomatik katılım" 
    part_points_list = list(dict.fromkeys(part_points_list)) 
    if len(part_points_list) == 1 and part_points_list[0].upper() == "J":
         method_category = "Uygulama üzerinden"; part_points_list = ["Juzdan uygulamasından 'Hemen Katıl' butonuna tıklayınız."]
    if not part_points_list and method_category == "Kampanya detaylarını kontrol ediniz.":
         part_points_list = ["Katılım yöntemi için kampanya detaylarını kontrol ediniz."]
    if len(part_points_list) == 1 and len(part_points_list[0]) > 35:
         method_category = part_points_list[0]
    elif found_app and found_sms:
         method_category = f"{match_app_text} veya {match_sms_text}"
    return method_category, part_points_list
def clean_kart_list_v25(kart_listesi):
    items_ve_split = re.split(r'\s+ve\s+', kart_listesi); final_list_intermediate = []
    for item in items_ve_split: final_list_intermediate.extend(item.split(','))
    final_list_cleaned = []
    for item in final_list_intermediate:
        item = re.sub(r'kartları$', '', item.strip(), flags=re.IGNORECASE)
        item = re.sub(r'kartlar$', '', item.strip(), flags=re.IGNORECASE)
        item = re.sub(r'kartı$', '', item.strip(), flags=re.IGNORECASE)
        item = re.sub(r'ı$', '', item.strip()); item = temizle_metin(item)
        if item and len(item) > 2: final_list_cleaned.append(item)
    return list(dict.fromkeys(final_list_cleaned))
def extract_valid_locations_v25(text):
    locations = []; match_locations = re.findall(r'(www\.[a-z0-9.-]+\.com(?:.tr)?)', text, re.IGNORECASE)
    if match_locations: locations.extend(list(dict.fromkeys(match_locations))) 
    match_store_list = re.search(r'Kampanya dahil olan üye işyeri listesi için tıklayınız\n(.*)', text, re.DOTALL)
    if match_store_list:
        list_text = match_store_list.group(1).strip()
        if list_text.startswith("İl Seçiniz:") or list_text.startswith("Firma Ünvanı"):
            if "Kampanyaya dahil üye işyerleri için kampanya sitesini ziyaret ediniz." not in locations:
                locations.append("Kampanyaya dahil üye işyerleri için kampanya sitesini ziyaret ediniz.")
        elif temizle_metin(list_text) not in locations: locations.append(temizle_metin(list_text))
    match_merchant_list = re.search(r'kampanyaya dahil ([\w\s]+) mağazalarında', text, re.IGNORECASE)
    if match_merchant_list:
        merchant_name = temizle_metin(match_merchant_list.group(1)) + " Mağazaları"
        if merchant_name not in locations: locations.append(merchant_name)
    return locations if locations else None
def clean_conditions_v25(text_list):
    cleaned = []
    for line in text_list:
        line = line.strip()
        if not line: continue
        if "Kampanya dahil olan üye işyeri listesi" in line: break 
        if "İl Seçiniz:" in line or "Bayi Ünvanı" in line: break
        cleaned.append(line)
    return cleaned
def map_difficulty_level_v25(participation_method_category):
    if participation_method_category in ["SMS ile katılım", "QR Kod okutma", "Uygulama üzerinden", "Başvuru gerekli", "Web sitesi üzerinden", "SMS ve Uygulama"]: return "Orta"
    elif "Otomatik katılım" in participation_method_category: return "Kolay"
    elif len(participation_method_category) > 35: return "Orta"
    else: return "Orta"

# --- Ayırt edici (wrapper) fonksiyonlar ---
def extract_merchant_wrapper(title, provider_name):
    # 'Business' da 'Axess' ile aynı deseni kullanır
    try:
        match = re.search(r"(Axess|Free)(?:’ye|'ye) özel\s+([^\s’']+)(?:’|'|’da|’de|'de|'da)", title, re.IGNORECASE)
        if match: return temizle_metin(match.group(2))
        match = re.search(r"([^\s’']+)(?:’|'|’da|’de|'de|'da)\s+(?:peşin|özel|indirim|chip-para|taksit)", title, re.IGNORECASE)
        if match: return temizle_metin(match.group(1))
    except Exception: pass
    return None

def extract_eligible_customers_wrapper(text, provider_name):
    try:
        match_specific_include = re.search(r'Kampanyadan\s+sadece\s+(.+?)\s+(?:yararlanabilir|faydalanabilir)', text, re.IGNORECASE)
        if match_specific_include:
            customers_text = temizle_metin(match_specific_include.group(1)); final_list_cleaned = clean_kart_list_v25(customers_text)
            if final_list_cleaned: return final_list_cleaned
        match_troy = re.search(r'((?:Axess TROY|Akbank Kart TROY|Free TROY)[\w\s,]*?)(?:ile\s+bu\s+kartlar|dahildir|dâhildir|geçerlidir)', text, re.IGNORECASE)
        if match_troy:
            customers_text = temizle_metin(match_troy.group(1)); final_list_cleaned = clean_kart_list_v25(customers_text)
            if final_list_cleaned: return final_list_cleaned
        match_inclusion = re.search(r'Kampanyaya\s+((?:[\w\s,]*)(?:Axess|Wings|Free|Ticari|Bank’O Card Axess|Akbank Kart)[\w\s,]*?)(?:ile\s+bu\s+kartlar|dahildir|dâhildir)', text, re.IGNORECASE)
        if match_inclusion:
            customers_text = temizle_metin(match_inclusion.group(1)); final_list_cleaned = clean_kart_list_v25(customers_text)
            if re.search(r"Bank(?:’|')O Card Axess.*?(?:dahil değildir|dâhil olmadığını|dâhil değildir)", text, re.IGNORECASE):
                if "Bank’O Card Axess" in final_list_cleaned: final_list_cleaned.remove("Bank’O Card Axess")
            if final_list_cleaned: return final_list_cleaned
    except Exception: pass
    # Varsayılanlar
    if "Free" in provider_name: return ["Free"]
    elif "Business" in provider_name: return ["Axess Business", "Ticari Kartlar"]
    else: return ["Axess", "Free", "Wings", "Ticari", "Bank'O Card Axess"]

# --- 3. ANA KAZIMA FONKSİYONLARI ---

def get_campaign_list(session, bank_config):
    """Aşama 1: API'den tüm kampanya URL'lerini çeker."""
    print(f"\n--- {bank_config['name']} Kampanyaları Çekiliyor ---")
    print("Aşama 1: Kampanya listesi API'den çekiliyor (Sayfalandırma başlıyor)...")
    campaign_urls = []
    page_number = 1
    headers = HEADERS_TEMPLATE.copy()
    headers['Referer'] = bank_config['referer_url']
    while True:
        params = bank_config['api_params'].copy()
        params['page'] = page_number
        print(f"Sayfa {page_number} taranıyor...")
        try:
            response = session.get(bank_config['api_list_url'], headers=headers, params=params, timeout=20)
            response.raise_for_status()
            html_content = response.text
            if 'kampanyadetay' not in html_content:
                print(f"Sayfa {page_number} boş geldi. Toplama tamamlandı.")
                break
            soup = BeautifulSoup(html_content, 'html.parser')
            links = soup.select(bank_config['list_item_selector']) 
            if not links:
                print(f"Sayfa {page_number} kampanya içermiyor. Toplama tamamlandı.")
                break
            found_new = False
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(bank_config['base_url'], href)
                    if full_url not in campaign_urls:
                        campaign_urls.append(full_url); found_new = True
            if not found_new and page_number > 1:
                print("Yeni kampanya bulunamadı. Durduruluyor."); break
            page_number += 1
            time.sleep(random.uniform(0.5, 1.0))
        except requests.exceptions.RequestException as e:
            print(f"API isteğinde hata (Sayfa {page_number}): {e}"); break
    print(f"Toplam {len(campaign_urls)} kampanya URL'si bulundu.")
    return campaign_urls

def get_campaign_details_arayanbuluyo_schema(session, url, bank_config):
    """Aşama 2: Tek bir kampanya sayfasını kazır."""
    print(f"Detaylar çekiliyor: {url.split('/')[-1][:50]}...")
    headers = HEADERS_TEMPLATE.copy()
    headers['Referer'] = bank_config['referer_url']
    try:
        response = session.get(url, headers=headers, timeout=(10, 20)) 
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"  [HATA] Detay sayfası yüklenemedi: {e}"); return None
    try:
        title_element = soup.select_one(bank_config['title_selector'])
        title = title_element.get_text(strip=True) if title_element else "Başlık Bulunamadı"
        image_element = soup.select_one(bank_config['image_selector'])
        image_url = image_element.get('src') if image_element else None
        if image_url and image_url.startswith('/'):
            image_url = urljoin(bank_config['image_base_url'], image_url) 
    except Exception as e:
        print(f"  [HATA] Başlık/Görsel alınamadı: {e}"); return None 
    try:
        details_element = soup.select_one(bank_config['detail_container_selector'])
        full_kosullar_text = ""; description = title; conditions_list = ["Detaylar Bulunamadı"]
        if details_element:
            full_kosullar_text = details_element.get_text(separator='\n', strip=True)
            desc_element = details_element.find('p')
            if desc_element: description = temizle_metin(desc_element.get_text())
            all_conditions_list = full_kosullar_text.split('\n')
            conditions_list = clean_conditions_v25(all_conditions_list)
    except Exception as e:
        print(f"  [UYARI] Koşullar ayrıştırılamadı: {e}")
        full_kosullar_text = title + " " + description; conditions_list = [description]
    
    provider_name = bank_config['name']
    category = tahmin_et_kategori_v25(title + ' ' + description)
    valid_from_tr, valid_until_tr = extract_dates_from_text_v25(full_kosullar_text)
    valid_from_iso, _ = format_tarih_iso_v25(valid_from_tr, is_end_date=False)
    valid_until_iso, _ = format_tarih_iso_v25(valid_until_tr, is_end_date=True)
    min_spend_int, earning_str, discount_str, discount_perc_int, max_discount_int = \
        extract_financials_v27(description + " " + full_kosullar_text)
    participation_method_str, participation_points_list = \
        extract_participation_v28(full_kosullar_text, title)
    difficulty_level_str = map_difficulty_level_v25(participation_method_str)
    eligible_customers_list = extract_eligible_customers_wrapper(full_kosullar_text, provider_name)
    merchant_str = extract_merchant_wrapper(title, provider_name)
    valid_locations_list = extract_valid_locations_v25(full_kosullar_text)
    
    if not merchant_str and valid_locations_list:
        try:
            for location in valid_locations_list:
                if "mağazaları" in location.lower(): merchant_str = temizle_metin(re.sub(r'mağazaları', '', location, flags=re.IGNORECASE)); break 
            if not merchant_str:
                 for location in valid_locations_list:
                     if "www." in location.lower(): merchant_str = temizle_metin(location.replace("www.", "")); break
        except Exception: pass
    if merchant_str and (merchant_str + " Mağazaları") not in (valid_locations_list or []):
         if not re.search(r'\.com(?:.tr)?$', merchant_str): 
             if valid_locations_list is None: valid_locations_list = []
             valid_locations_list.append(merchant_str + " Mağazaları")
             valid_locations_list = list(dict.fromkeys(valid_locations_list))

    # --- Final JSON Objesi (ID YOK) ---
    kampanya_objesi = {
        "title": title, "provider": provider_name,
        "category": category, "image": image_url, "images": [image_url] if image_url else [],
        "featured": False, "description": description, "url": url, "views": 0,
        "discount": discount_str, "earning": earning_str,
        "min_spend": min_spend_int,
        "max_discount": max_discount_int,
        "discount_percentage": discount_perc_int,
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "valid_from": valid_from_iso,
        "valid_until": valid_until_iso,
        "votes_up": 0,
        "votes_down": 0,
        "participation_method": participation_method_str,
        "participation_points": participation_points_list,
        "conditions": conditions_list, 
        "eligible_customers": eligible_customers_list,
        "valid_locations": valid_locations_list,
        "merchant": merchant_str,
        "difficulty_level": difficulty_level_str,
        "source_url": bank_config['base_url']
    }
    return kampanya_objesi


# --- 4. ANA ÇALIŞTIRMA KISMI (Birleşik) ---

if __name__ == "__main__":
    print(f"Akbank (Axess, Free & Business) Birleşik Scraper (v1) başlıyor...")
    start_time = time.time()
    
    all_campaign_data = [] 
    
    with requests.Session() as session:
        
        for bank_config in BANK_CONFIGS:
            all_campaign_urls = get_campaign_list(session, bank_config)
            
            if all_campaign_urls:
                print(f"\n--- {bank_config['name']} için {len(all_campaign_urls)} adet kampanya detayı çekiliyor... ---\n")
                
                for url in all_campaign_urls:
                    data = get_campaign_details_arayanbuluyo_schema(session, url, bank_config)
                    
                    if data:
                        all_campaign_data.append(data)
                    
                    sleep_time = random.uniform(0.7, 1.5)
                    print(f"   ... {sleep_time:.2f} saniye bekleniyor ...")
                    time.sleep(sleep_time) 
            else:
                print(f"{bank_config['name']} için hiç kampanya URL'si bulunamadı.")
    
    # Tüm veriyi tek dosyaya kaydet
    if all_campaign_data:
        try:
            with open(JSON_FILE_NAME, 'w', encoding='utf-8') as f:
                json.dump(all_campaign_data, f, ensure_ascii=False, indent=4)
            
            full_path = os.path.abspath(JSON_FILE_NAME)
            elapsed_time = time.time() - start_time
            
            print("\n" + "="*50)
            print(f"🎉 BİRLEŞİK İŞLEM BAŞARILI! 🎉")
            print(f"Toplam {len(all_campaign_data)} kampanya (Axess + Free + Business) şu dosyaya kaydedildi:")
            print(f"{full_path}")
            print(f"(Toplam süre: {elapsed_time:.2f} saniye)")
            print("="*50)
        
        except IOError as e:
            print(f"\n HATA: JSON dosyası yazılırken bir hata oluştu: {e}")
            
    else:
        print("Hiçbir siteden kampanya verisi çekilemedi. Script durduruldu.")