import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import json
import os
import re
from datetime import datetime
import random

# --- 1. AYARLAR (v5.4 - Finansal & Kart Mantığı Düzeltildi / Stabil JSON) ---
LIST_API_URL = "https://www.yapikrediplay.com.tr/api/campaigns?campaignSectorId=dfe87afe-9b57-4dfd-869b-c87dd00b85a1&campaignSectorKey=tum-kampanyalar"
BASE_URL = "https://www.yapikrediplay.com.tr"
REFERER_URL = "https://www.yapikrediplay.com.tr/kampanyalar"
JSON_FILE_NAME = "play_v5.4_duzeltilmis.json" # <--- YENİ ÇIKTI DOSYASI
IMPORT_SOURCE_NAME = "Play Card (Yapı Kredi)"

# v5.4 AYARLAR
MAX_RETRIES = 3 
REQUEST_TIMEOUT = 20 
SLEEP_MIN = 1.0 
SLEEP_MAX = 2.0 

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36",
    "Referer": REFERER_URL, 
    "x-requested-with": "XMLHttpRequest", 
    "accept": "*/*"
}

# --- 2. YARDIMCI FONKSİYONLAR (v5.4 - JSON Korumalı "Whitelist" + Akıllı Mantık) ---

def temizle_metin(text):
    """
    v4.0 - "Whitelist" Temizleyici:
    Sadece "iyi" (geçerli) karakterlere (whitelist) izin verir.
    'Line 669' hatasını %100 çözer.
    """
    if not text:
        return ""
    
    try:
        # 1. Adım: Sadece geçerli UTF-8 karakterlerine izin ver (Kontrol karakterleri hariç)
        text = re.sub(r'[^\x20-\x7E\u00A0-\uFFFF]', ' ', text)
        # 2. Adım: Tüm boşlukları (\n, \t, \r dahil) tek boşluğa indirge
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except (TypeError, AttributeError):
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
    
    tarih_str = re.sub(r'(\d+)\.(\d+)', r'\1 \2', tarih_str) 

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
def tahmin_et_kategori_v25_play_adapted(text):
    text = text.lower()
    if re.search(r'oyun|steam|e-spor|twitch|playstation|riot games|zula', text): return 'Oyun & E-Spor'
    if re.search(r'yakıt|akaryakıt|benzin|shell|opet|bp', text): return 'Yakıt'
    if re.search(r'market|migros|carrefour|a101|şok|bim|gıda', text): return 'Market'
    if re.search(r'restoran|yemek|cafe|restaurant|burger|pizza|yemeksepeti', text): return 'Restoran & Kafe'
    if re.search(r'elektronik|teknoloji|mediamarkt|itopya|dyson|teknosa|gürgençler|monster|vestel', text): return 'Elektronik'
    if re.search(r'giyim|moda|ayakkabı|lcwaikiki|defacto|beymen|ipekyol|twist|koton|flo|columbia|desa|lacoste|ecrou|reebok|lumberjack|nine west|in street|polaris', text): return 'Giyim & Moda'
    if re.search(r'\bev\b|mobilya|dekorasyon|ikea|istikbal|bellona|işbir yatak|koçtaş|karaca|schafer|evidea|özdilek|idas|ider|korkmaz|vivense|alfemo', text): return 'Ev & Yaşam'
    if re.search(r'trendyol|hepsiburada|amazon|online|e-ticaret|n11|pazarama', text): return 'Online Alışveriş' 
    if re.search(r'seyahat|otel|tatil|uçak|turizm|duty.free|mil|puan|bilet|tatilsepeti|obilet|setur|touristica|enuygun', text): return 'Seyahat'
    if re.search(r'sinema|tiyatro|konser|eğlənce|biletix|passo|theatreclix', text): return 'Eğlence'
    if re.search(r'kozmetik|güzellik|bakım|eczane|sağlık|watsons|gratis', text): return 'Sağlık & Güzellik'
    if re.search(r'spor|outdoor|decathlon|adidas|nike|puma', text): return 'Spor & Outdoor'
    if re.search(r'kitap|kırtasiye|dr|idefix|nezih', text): return 'Kitap & Kırtasiye'
    return 'Diğer'
def extract_dates_from_text_v25(text):
    valid_from, valid_until = None, None; text = temizle_metin(text) 
    try:
        match = re.search(r'(\d{1,2}[\.\s]+[\wıöüçğş]+(?:\s+\d{4})?)\s*(?:-|–)\s*(\d{1,2}[\.\s]+[\wıöüçğş]+\s+\d{4})', text, re.IGNORECASE)
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

def extract_financials_v5_3_play_adapted(text):
    """
    v5.4 - Finansal mantık hatalarını (ID 24) düzelten son sürüm.
    """
    min_spend_int, max_discount_int, discount_perc_int = None, None, None
    final_earning, final_discount = None, None
    finance_text = text.lower()
    taksit_str, worldpuan_str, indirim_str = None, None, None
    spend_calculated = False

    # v5.3 Düzeltmesi: 'TL'ye' gibi ekleri de yakalamak için suffix (opsiyonel)
    tl_suffix = r"(?:tl|₺)(?:'ye|’ye|'e|’e|'a|’a)?"

    # 1. KAZANÇLARI BUL
    all_worldpuan_vals = []
    pattern_worldpuan = re.findall(r'(\d+[\d.,]*)\s*' + tl_suffix + r'\s*(?:worldpuan|puan|hediye|iade|değerinde)', finance_text, re.IGNORECASE)
    if not pattern_worldpuan: pattern_worldpuan = re.findall(r'(\d+[\d.,]*)\s*' + tl_suffix + r'.{0,15}?(?:worldpuan|puan|hediye|iade|değerinde)', finance_text, re.IGNORECASE)
    for match in pattern_worldpuan:
        val_str = match[0] if isinstance(match, tuple) else match
        try: all_worldpuan_vals.append(int(val_str.replace('.','').replace(',','')))
        except (ValueError, IndexError): pass
    if all_worldpuan_vals: best_worldpuan_val = max(all_worldpuan_vals); worldpuan_str = f"{format_rakam(best_worldpuan_val)} TL Worldpuan"

    taksit_numbers = []
    match_taksit = re.findall(r'(?<!ticari\s)(?<!azami\s)(?<!en fazla\s)(\d+)\s*(?:aya varan|ay)?\s*taksit', finance_text, re.IGNORECASE)
    if match_taksit: taksit_numbers.extend(map(int, match_taksit))
    if taksit_numbers: taksit_str = f"{max(taksit_numbers)} Taksit"
    
    match_percent = re.search(r'%\s*(\d+)', finance_text, re.IGNORECASE)
    if match_percent: discount_perc_int = int(match_percent.group(1)); indirim_str = f"%{discount_perc_int} İndirim"
    
    match_tl_indirim = re.findall(r'(\d+[\d.,]*)\s*' + tl_suffix + r'\s*indirim', finance_text, re.IGNORECASE)
    if match_tl_indirim and not (indirim_str and '%' in indirim_str): 
        tl_indirim_vals = [int(m.replace('.','').replace(',','')) for m in match_tl_indirim];
        if tl_indirim_vals: indirim_str = f"{format_rakam(max(tl_indirim_vals))} TL İndirim"
    
    if worldpuan_str: final_earning = worldpuan_str
    elif indirim_str: final_earning = indirim_str
    if taksit_str: final_discount = taksit_str
    
    # === v5.4 DÜZELTMESİ (ID 24) ===
    # 2. MAKSİMUM KAZANCI BUL (Önce "toplam" ara, sonra "en fazla")
    max_earning_match = re.search(r"(?:toplamda|toplam|ayl\u0131k toplam)\s*([\d\.,]+)\s*" + tl_suffix, finance_text)
    if not max_earning_match: # Eğer "toplam" bulamazsa, "en fazla" ara
        max_earning_match = re.search(r"(?:en fazla|maksimum)\s*([\d\.,]+)\s*" + tl_suffix, finance_text)
    
    if max_earning_match: 
        max_discount_int = int(max_earning_match.group(1).replace('.','').replace(',',''))
    # === v5.4 DÜZELTMESİ SONU ===
    elif worldpuan_str and not max_discount_int: 
         try: max_discount_int = int(re.search(r"([\d\.]+)", worldpuan_str.replace('.','')).group(1))
         except Exception: pass
    elif indirim_str and "TL" in indirim_str and not max_discount_int: 
         try: max_discount_int = int(re.search(r"([\d\.]+)", indirim_str.replace('.','')).group(1))
         except Exception: pass

    # 3. MİNİMUM HARCAMAYI HESAPLA (Öncelik sırasıyla)
    
    # KURAL 1: (ID 28, ID 24) "%X indirim... toplam Y TL"
    try:
        # v5.3 DÜZELTME: Ayrı ayrı bul ve hesapla (daha güvenli)
        if discount_perc_int is not None and max_discount_int is not None and not spend_calculated:
            # Sadece %'li indirim ve toplam TL limiti varsa hesapla
            if indirim_str and indirim_str.startswith("%"): 
                min_spend_int = int(max_discount_int / (discount_perc_int / 100)) # 1500 (ID 24)
                spend_calculated = True
    except Exception: pass

    # KURAL 2: (ID 6 - Opet) "ilk X... sonraki her Y... Z puan... toplam T puan"
    try:
        pattern_opet = re.search(r'ilk\s*([\d\.,]+)\s*' + tl_suffix + r'.*?sonraki\s*her\s*([\d\.,]+)\s*' + tl_suffix + r'.*?([\d\.,]+)\s*' + tl_suffix + r'.*?(?:toplamda|toplam)\s*([\d\.,]+)\s*' + tl_suffix, finance_text, re.IGNORECASE)
        if pattern_opet and not spend_calculated:
            g = [s.replace('.','').replace(',','') for s in pattern_opet.groups()]
            trigger_spend = int(g[0]); spend_per_tx = int(g[1]); earn_per_tx = int(g[2]); total_earn = int(g[3])
            if earn_per_tx > 0:
                num_tx = total_earn / earn_per_tx
                min_spend_int = int((num_tx * spend_per_tx) + trigger_spend) # 13750
                spend_calculated = True
    except Exception: pass

    # KURAL 3: (ID 9 - Restoran) "her X... Y puan... ek A puan... toplam Z puan"
    try:
        pattern_ek = re.search(r'her\s*([\d\.,]+)\s*' + tl_suffix + r'.*?([\d\.,]+)\s*' + tl_suffix + r'.*?ek\s*([\d\.,]+)\s*' + tl_suffix + r'.*?(?:toplamda|toplam)\s*([\d\.,]+)\s*' + tl_suffix, finance_text, re.IGNORECASE)
        if pattern_ek and not spend_calculated:
            g = [s.replace('.','').replace(',','') for s in pattern_ek.groups()]
            spend_per_tx = int(g[0]); base_earn = int(g[1]); ek_earn = int(g[2]); total_earn = int(g[3])
            total_earn_per_tx = base_earn + ek_earn
            if total_earn_per_tx > 0:
                num_tx = total_earn / total_earn_per_tx
                min_spend_int = int(num_tx * spend_per_tx) # 6000
                spend_calculated = True
    except Exception: pass
    
    # KURAL 4: (ID 27 - e-ticaret) "her X... Y puan... toplam Z puan"
    try:
        # v5.3 DÜZELTME: "ve üzeri" gibi ifadeleri atlamak için (\s*(?:ve \S+)?.*?) eklendi
        pattern_repeating = re.search(r'her\s*([\d\.,]+)\s*' + tl_suffix + r'\s*(?:ve \S+)?.*?([\d\.,]+)\s*' + tl_suffix + r'.*?(?:toplamda|toplam)\s*([\d\.,]+)\s*' + tl_suffix, finance_text, re.IGNORECASE)
        if pattern_repeating and not spend_calculated:
            g = [s.replace('.','').replace(',','') for s in pattern_repeating.groups()]
            spend_per_tx = int(g[0]); earn_per_tx = int(g[1]); total_earn = int(g[2])
            if earn_per_tx > 0:
                num_tx = total_earn / earn_per_tx
                min_spend_int = int(num_tx * spend_per_tx) # 750
                spend_calculated = True
    except Exception: pass

    # KURAL 5: (Standart) "X TL ve üzeri..." (En düşük öncelikli)
    try:
        if not spend_calculated:
            all_spends_int = []
            pattern_spends = re.findall(r'(\d+[\d.,]*)\s*' + tl_suffix + r'\s*(?:ve üzeri|üzeri|harcama|alışveriş)', finance_text, re.IGNORECASE)
            if pattern_spends:
                for spend_str in pattern_spends: all_spends_int.append(int(spend_str.replace('.','').replace(',','')))
            if all_spends_int: 
                min_spend_int = min(all_spends_int) 
                spend_calculated = True
    except Exception: pass 

    return min_spend_int, final_earning, final_discount, discount_perc_int, max_discount_int

def extract_merchant_v25_play_adapted(title):
    try:
        match = re.search(r"Play(?:’e|'e) özel\s+([^\s’']+)(?:’|'|’da|’de|'de|'da)", title, re.IGNORECASE)
        if match: return temizle_metin(match.group(1))
        match = re.search(r"([^\s’']+)(?:’|'|’da|’de|'de|'da)\s+(?:peşin|özel|indirim|worldpuan|taksit)", title, re.IGNORECASE)
        if match: return temizle_metin(match.group(1))
    except Exception: pass
    return None

def extract_participation_v28_play_adapted(text, title):
    part_points_list = []
    method_category = "Kampanya detaylarını kontrol ediniz."
    found_app = False
    found_sms = False
    match_app_text = ""
    match_sms_text = ""

    match_app = re.search(r'((?:World\s*Mobil|Yapı\s*Kredi\s*Mobil).*?(?:Hemen Katıl|butonuna|üzerinden|sayfasındaki|uygulamasından).*?(?:tıkla|katıl)\w*)', text, re.IGNORECASE)
    if match_app:
        match_app_text = temizle_metin(match_app.group(1))
        part_points_list.append(match_app_text)
        method_category = "Uygulama üzerinden"
        found_app = True
    
    match_sms = re.search(r'\s*([A-Z0-9İÖÜŞĞÇ]+)\s*yazıp\s*.*?(\d{4})\s*\'?(?:e|ye|a|’e|’a)\s*gönder', text, re.IGNORECASE)
    if not match_sms:
        match_sms = re.search(r'SMS\s*ile.*?için\s*([A-Z0-9İÖÜŞĞÇ]+)\s*yazıp.*?(\d{4})\s*\'?(?:e|ye|a|’e|’a)', text, re.IGNORECASE)
        
    if match_sms:
        sms_kod = match_sms.group(1)
        sms_num = match_sms.group(2)
        match_sms_text = temizle_metin(f"{sms_kod} yazıp {sms_num}'a SMS gönderilmelidir.")
        part_points_list.append(match_sms_text)
        found_sms = True
        
    if found_app and found_sms:
        method_category = "SMS ve Uygulama"
    elif found_sms and not found_app:
        method_category = "SMS ile katılım"
            
    match_auto = re.search(r'(otomatik katılım|herhangi bir işlem gerekmez|otomatik olarak katıl)', text, re.IGNORECASE)
    if match_auto and not found_app and not found_sms:
        part_points_list.append(temizle_metin(match_auto.group(0))); method_category = "Otomatik katılım" 

    part_points_list = list(dict.fromkeys(part_points_list)) 
    
    if not part_points_list and method_category == "Kampanya detaylarını kontrol ediniz.":
         part_points_list = ["Katılım yöntemi için kampanya detaylarını kontrol ediniz."]
    
    if len(part_points_list) == 1 and len(part_points_list[0]) > 35:
         method_category = part_points_list[0]
    elif found_app and found_sms:
         method_category = f"{match_app_text} veya {match_sms_text}"

    return method_category, part_points_list

# === v5.4 KART TEMİZLEME DÜZELTMESİ (ID 1, ID 4) ===
def clean_kart_list_v5_4(kart_listesi):
    """v5.4 - 'kredi kartı'nı korur, 'Yapı Kredi'yi temizler, 'veya'yı ayırır"""
    
    # "ve" veya "veya" ile ayır
    items_ve_split = re.split(r'\s+(?:ve|veya)\s+', kart_listesi); 
    final_list_intermediate = []
    
    # Virgül ile ayır
    for item in items_ve_split: 
        final_list_intermediate.extend(item.split(','))
        
    final_list_cleaned = []
    
    for item in final_list_intermediate:
        # Önce 'temizle_metin' ile bozuk karakterleri at
        item = temizle_metin(item)
        
        # === v5.4 YENİ TEMİZLİK ===
        # "Yapı Kredi" kelimesini her zaman kaldır
        item = re.sub(r'Yapı Kredi', '', item.strip(), flags=re.IGNORECASE)
        # "bireysel" kelimesini her zaman kaldır
        item = re.sub(r'bireysel', '', item.strip(), flags=re.IGNORECASE)
        
        # "kredi" kelimesini, "kredi kart" içinde geçmiyorsa kaldır
        if 'kredi kart' not in item.lower():
            item = re.sub(r'kredi', '', item.strip(), flags=re.IGNORECASE)
        # === v5.4 YENİ TEMİZLİK SONU ===

        # Ekleri temizle (daha az agresif)
        item = re.sub(r'kartlar\u0131$', 'kartları', item.strip(), flags=re.IGNORECASE) # kartları -> kartları (normalize)
        item = re.sub(r'kartlar$', 'kartlar', item.strip(), flags=re.IGNORECASE) # kartlar -> kartlar (normalize)
        item = re.sub(r'kart\u0131$', 'kartı', item.strip(), flags=re.IGNORECASE) # kartı -> kartı (normalize)
        
        # Sadece son ekleri temizle
        item = re.sub(r'\’lar$', '', item.strip(), flags=re.IGNORECASE) 
        item = re.sub(r'\’ları$', '', item.strip(), flags=re.IGNORECASE) 
        item = re.sub(r'\’u$', '', item.strip(), flags=re.IGNORECASE) 
        item = re.sub(r'\s+dahildir$', '', item.strip(), flags=re.IGNORECASE)
        
        item = item.strip()
        
        if item and len(item) > 2: 
            final_list_cleaned.append(item)
            
    return list(dict.fromkeys(final_list_cleaned))
# === v5.4 KART TEMİZLEME DÜZELTMESİ SONU ===


# === v5.4 KART ÇIKARIM DÜZELTMESİ (ID 1, ID 4) ===
def extract_eligible_customers_v5_4_play_adapted(text):
    """
    v5.4 - ID 1 ("ile ödeme yapılmalıdır") ve ID 4 ("Play kredi kartları")
    hatalarını düzelten ve v5.4 temizleyiciyi çağıran sürüm.
    """
    try:
        # KURAL 1: "sadece" veya "yalnızca" (En spesifik) (ID 4)
        match_specific_include = re.search(
            r'(?:Kampanyadan|Kampanyaya)\s+(?:sadece|yaln\u0131zca)\s+(.+?)\s+(?:d\u00e2hildir|dahildir|ge\u00e7erlidir|yararlanabilir|faydalanabilir)',
            text, re.IGNORECASE
        )
        if match_specific_include:
            customers_text = match_specific_include.group(1)
            final_list_cleaned = clean_kart_list_v5_4(customers_text) # <-- v5.4 TEMİZLEYİCİ
            if final_list_cleaned:
                return final_list_cleaned 

        # KURAL 2: Standart "dahildir" kuralı
        match_inclusion = re.search(
            r'Kampanyaya\s+((?:[\w\s,]*)(?:Play|World|Yapı Kredi|Bireysel|TLcard|Albaraka|Anadolubank|Vakıfbank)[\w\s,]*?)(?:ile\s+bu\s+kartlar|dahildir|dâhildir)', 
            text, 
            re.IGNORECASE
        )
        if match_inclusion:
            customers_text = match_inclusion.group(1)
            final_list_cleaned = clean_kart_list_v5_4(customers_text) # <-- v5.4 TEMİZLEYİCİ
            
            # KURAL 3: "dahil değildir" istisnası
            if re.search(r"(Bankomat|Ticari|Nakit|Ön ödemeli|Play Genç)[\w\s,]*?(?:dahil değildir|dâhil olmadığını|dâhil değildir|kapsam\u0131nda \u00f6d\u00fcllendirilmez)", text, re.IGNORECASE):
                final_list_cleaned = [kart for kart in final_list_cleaned if 'Ticari' not in kart and 'Play Genç' not in kart]
            
            if final_list_cleaned:
                return final_list_cleaned
        
        # KURAL 3: (ID 1) "...kartları ile ödeme yapılmalıdır"
        match_payment_cards = re.search(
            r'((?:[\w\s,]*)(?:kart\u0131|kartlar|kart)(?:[\w\s,]|veya)*?)\s+ile\s+(?:ödeme yap\u0131lmal\u0131d\u0131r|harcama yap\u0131lmal\u0131d\u0131r)',
            text, re.IGNORECASE
        )
        if match_payment_cards:
            customers_text = match_payment_cards.group(1)
            final_list_cleaned = clean_kart_list_v5_4(customers_text) # <-- v5.4 TEMİZLEYİCİ
            if final_list_cleaned:
                return final_list_cleaned

    except Exception:
        pass
    
    return ["Play Card"] # Hiçbir şey bulamazsa varsayılan
# === v5.4 KART ÇIKARIM DÜZELTMESİ SONU ===


def extract_valid_locations_v25(text):
    locations = []; match_locations = re.findall(r'(www\.[a-z0-9.-]+\.com(?:.tr)?)', text, re.IGNORECASE)
    if match_locations: locations.extend(list(dict.fromkeys(match_locations))) 
    
    match_store_list = re.search(r'(?:Üye İşyerleri|Sektör ve Üye İşyerleri)\s*<ul>\s*(.*?)\s*</ul>', text, re.DOTALL | re.IGNORECASE)
    if match_store_list:
        list_html = match_store_list.group(1)
        list_soup = BeautifulSoup(list_html, 'html.parser')
        store_items = [temizle_metin(li.text) for li in list_soup.find_all('li')]
        if store_items:
            locations.extend(store_items)

    match_merchant_list = re.search(r'kampanyaya dahil ([\w\s]+) mağazalarında', text, re.IGNORECASE)
    if match_merchant_list:
        merchant_name = temizle_metin(match_merchant_list.group(1)) + " Mağazaları"
        if merchant_name not in locations: locations.append(merchant_name)
    
    locations = list(dict.fromkeys(locations))
    return locations if locations else None
def clean_conditions_v25(text_list):
    cleaned = []
    for line in text_list:
        if not line: continue
        if len(line) < 15: continue
        cleaned.append(line)
    return cleaned
def map_difficulty_level_v25(participation_method_category):
    if participation_method_category in ["SMS ile katılım", "QR Kod okutma", "Uygulama üzerinden", "Başvuru gerekli", "Web sitesi üzerinden", "SMS ve Uygulama"]: return "Orta"
    elif "Otomatik katılım" in participation_method_category: return "Kolay"
    elif len(participation_method_category) > 35: return "Orta"
    else: return "Orta"


# --- 3. ANA KAZIMA FONKSİYONLARI (Play + v28 Schema) ---

def get_campaign_list_from_api(session):
    print("Aşama 1: Play API'den kampanya listesi çekiliyor (Sayfalandırma başlıyor)...")
    all_campaigns_from_api = []
    current_page = 1
    
    while True:
        print(f"   -> Sayfa {current_page} çekiliyor...")
        current_headers = HEADERS.copy()
        current_headers["page"] = str(current_page) 
        
        try:
            response = session.get(LIST_API_URL, headers=current_headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            api_data = response.json()
            
            campaign_list_on_this_page = api_data.get('Items')
            
            if not campaign_list_on_this_page:
                print(f"   -> Sayfa {current_page} boş geldi. Toplam {current_page - 1} sayfa çekildi.")
                break
                
            print(f"   -> Sayfa {current_page} başarıyla çekildi ({len(campaign_list_on_this_page)} kampanya bulundu).")
            all_campaigns_from_api.extend(campaign_list_on_this_page)
            current_page += 1
            time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))
            
        except requests.exceptions.RequestException as e:
            print(f"API isteğinde hata (Sayfa {current_page}): {e}")
            break
            
    print(f"\n✅ API'den Toplam {len(all_campaigns_from_api)} adet kampanya bulundu!")
    if len(all_campaigns_from_api) == 0:
        return {}

    url_map = {} # {url: (image_url, api_title)}
    for item in all_campaigns_from_api:
        try:
            detail_path = temizle_metin(item.get('Url'))
            image_path = temizle_metin(item.get('ImageUrl'))
            api_title = temizle_metin(item.get('SpotTitle', item.get('PageTitle', item.get('Title'))))

            if not detail_path: continue
            url = urljoin(BASE_URL, detail_path) 

            if not image_path: continue
            image_url = urljoin(BASE_URL, image_path.split('?')[0])
            
            if url not in url_map:
                url_map[url] = (image_url, api_title) 
                
        except Exception as e:
            print(f"❌ HATA 1 (API Yapı Hatası): API listesi işlenemedi: {e}")

    print(f"Toplam {len(url_map)} benzersiz kampanya URL'si bulundu.")
    return url_map


def get_campaign_details_snake_case_schema(session, url, image_url, api_title, campaign_id):
    
    for attempt in range(MAX_RETRIES):
        print(f"Detaylar çekiliyor (ID: {campaign_id}, Deneme: {attempt + 1}/{MAX_RETRIES}): {url.split('/')[-1][:50]}...")
        try:
            response = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT) 
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            break
        except requests.exceptions.RequestException as e:
            print(f"  [HATA] Network hatası (ID: {campaign_id}): {e}")
            if attempt < MAX_RETRIES - 1:
                wait_time = (attempt + 1) * 2 
                print(f"     ... {wait_time} saniye sonra yeniden denenecek ...")
                time.sleep(wait_time)
            else:
                print(f"  [KRİTİK HATA] {MAX_RETRIES} deneme başarısız. (ID: {campaign_id}) atlanıyor.")
                return None 

    try:
        title = api_title if api_title else "Başlık Bulunamadı" 
        image_url = image_url 
        
        description = ""
        desc_elem = soup.select_one('meta[name="description"]')
        if desc_elem and desc_elem.get('content'):
            description = temizle_metin(desc_elem['content']) 
        if not description or len(description) < 20:
            description = title

    except Exception as e:
        print(f"  [HATA] Başlık/Görsel alınamadı (ID: {campaign_id}): {e}")
        return None 

    try:
        details_element = soup.select_one('.campaign-terms')
        full_kosullar_text = ""
        conditions_list = ["Detaylar Bulunamadı"]
        
        if details_element:
            all_conditions_list = [temizle_metin(item.text) for item in details_element.select('ul > li, p') if item.text and len(item.text.strip()) > 10]
            conditions_list = clean_conditions_v25(all_conditions_list)
            full_kosullar_text = temizle_metin(details_element.get_text(separator=' ', strip=True))
        else:
            print(f"  [UYARI] '.campaign-terms' bulunamadı (ID: {campaign_id}). Fallback aranıyor...")
            content_div = soup.select_one('.sub-content') 
            if content_div:
                all_conditions_list = [temizle_metin(item.text) for item in content_div.select('ul > li, p') if item.text and len(item.text.strip()) > 10]
                conditions_list = clean_conditions_v25(all_conditions_list)
                full_kosullar_text = temizle_metin(content_div.get_text(separator=' ', strip=True))
            else:
                print(f"  [UYARI] Fallback de bulunamadı. Body kullanılacak.")
                raw_text = soup.body.get_text(separator=' ', strip=True) if soup.body else (title + " " + description)
                full_kosullar_text = temizle_metin(raw_text) 
                conditions_list = [description] 

        if not full_kosullar_text:
             full_kosullar_text = title + " " + description 
             
    except Exception as e:
        print(f"  [UYARI] Koşullar ayrıştırılamadı (ID: {campaign_id}): {e}")
        full_kosullar_text = title + " " + description 
        conditions_list = [description]

    # --- v5.4 Akıllı Fonksiyonlarını Çağırma ---
    
    try:
        category = tahmin_et_kategori_v25_play_adapted(title + ' ' + description)
    except Exception: category = "Diğer"

    try:
        valid_from_tr, valid_until_tr = extract_dates_from_text_v25(full_kosullar_text)
        valid_from_iso, valid_from_obj = format_tarih_iso_v25(valid_from_tr, is_end_date=False)
        valid_until_iso, valid_until_obj = format_tarih_iso_v25(valid_until_tr, is_end_date=True)
        
        if valid_until_obj and not valid_from_obj:
            start_of_month = valid_until_obj.replace(day=1)
            valid_from_iso = start_of_month.strftime("%Y-%m-%dT00:00:00Z")
    except Exception as e:
        print(f"  [UYARI] Tarih ayrıştırılamadı (ID: {campaign_id}): {e}")
        valid_from_iso, valid_until_iso = None, None

    try:
        # v5.3 Düzeltmesi: 'title' değişkeni analiz edilecek metne eklendi
        combined_financial_text = title + " " + description + " " + full_kosullar_text
        
        # v5.4 - DÜZELTİLMİŞ FİNANSAL FONKSİYON
        min_spend_int, earning_str, discount_str, discount_perc_int, max_discount_int = \
            extract_financials_v5_3_play_adapted(combined_financial_text)
    except Exception as e:
        print(f"  [UYARI] Finansal veriler ayrıştırılamadı (ID: {campaign_id}): {e}")
        min_spend_int, earning_str, discount_str, discount_perc_int, max_discount_int = None, None, None, None, None

    try:
        participation_method_str, participation_points_list = \
            extract_participation_v28_play_adapted(full_kosullar_text, title)
        difficulty_level_str = map_difficulty_level_v25(participation_method_str)
    except Exception as e:
        print(f"  [UYARI] Katılım ayrıştırılamadı (ID: {campaign_id}): {e}")
        participation_method_str = "Kampanya detaylarını kontrol ediniz."
        participation_points_list = ["Katılım yöntemi için kampanya detaylarını kontrol ediniz."]
        difficulty_level_str = "Orta"

    try:
        # v5.4 - DÜZELTİLMİŞ MÜŞTERİ FONKSİYONU
        eligible_customers_list = extract_eligible_customers_v5_4_play_adapted(full_kosullar_text)
    except Exception as e:
        print(f"  [UYARI] Müşteri listesi ayrıştırılamadı (ID: {campaign_id}): {e}")
        eligible_customers_list = ["Play Card"]

    try:
        merchant_str = extract_merchant_v25_play_adapted(title)
        valid_locations_list = extract_valid_locations_v25(full_kosullar_text)
    except Exception as e:
        print(f"  [UYARI] Lokasyon/Marka ayrıştırılamadı (ID: {campaign_id}): {e}")
        merchant_str = None; valid_locations_list = None


    # --- Final JSON Objesi (Supabase 'snake_case' uyumlu) ---
    kampanya_objesi = {
        "id": campaign_id, "title": title, "provider": IMPORT_SOURCE_NAME,
        "category": category, 
        "image": image_url, 
        "images": [image_url] if image_url else [],
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
        "source_url": BASE_URL
    }
    return kampanya_objesi


# --- 4. ANA ÇALIŞTIRMA KISMI (Düzeltmelerle) ---

if __name__ == "__main__":
    print(f"Play Scraper (v5.4 - Ak\u0131ll\u0131 Mant\u0131k / STAB\u0130L JSON) ba\u015fl\u0131yor...")
    start_time = time.time()
    with requests.Session() as session:
        
        all_campaign_url_map = get_campaign_list_from_api(session)
        
        if all_campaign_url_map:
            print(f"\n--- API'den {len(all_campaign_url_map)} adet kampanya bulundu. Zengin detaylar çekiliyor... ---\n")
            all_campaign_data = []
            id_counter = 1 
            
            for url, (image_url, api_title) in all_campaign_url_map.items():
                data = get_campaign_details_snake_case_schema(session, url, image_url, api_title, id_counter)
                if data:
                    all_campaign_data.append(data)
                
                id_counter += 1 
                
                sleep_time = random.uniform(SLEEP_MIN, SLEEP_MAX)
                print(f"   ... {sleep_time:.2f} saniye bekleniyor ...")
                time.sleep(sleep_time) 
                
            if all_campaign_data:
                try:
                    with open(JSON_FILE_NAME, 'w', encoding='utf-8') as f:
                        # "ensure_ascii=False" YOK. Bu, JSON'u %100 stabil yapar.
                        json.dump(all_campaign_data, f, indent=4)
                        
                    full_path = os.path.abspath(JSON_FILE_NAME)
                    elapsed_time = time.time() - start_time
                    print("\n" + "="*50)
                    print(f"🎉 BAŞARILI! (v5.4 - Play Akıllı Sürüm) 🎉")
                    print(f"Toplam {len(all_campaign_data)} kampanya (Supabase 'snake_case' uyumlu) şu dosyaya kaydedildi:")
                    print(f"{full_path}")
                    print(f"(Dosya '\u015f' gibi kodlar içerebilir, bu normaldir ve stabildir.)")
                    print(f"(Toplam süre: {elapsed_time:.2f} saniye)")
                    print("="*50)
                except IOError as e:
                    print(f"\n HATA: JSON dosyası yazılırken bir hata oluştu: {e}")
                except Exception as e: 
                    print(f"\n HATA: JSON oluşturulurken beklenmedik bir hata oluştu: {e}")
        else:
            print("Hiç kampanya URL'si bulunamadı. Script durduruldu.")