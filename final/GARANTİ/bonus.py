import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import json
import os
import re
from datetime import datetime
import random
import math

# --- 1. AYARLAR (V13 - Matematiksel Düzeltme) ---
BASE_URL = "https://www.bonus.com.tr"
CAMPAIGN_LIST_URL = "https://www.bonus.com.tr/kampanyalar"
JSON_FILE_NAME = "bonus_kampanyalar_v13_fixed.json"
IMPORT_SOURCE_NAME = "Bonus (Garanti BBVA)"
CAMPAIGN_LIMIT = 999 

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
}

# --- 2. YARDIMCI FONKSİYONLAR ---

def temizle_metin(text):
    if not text: return ""
    try:
        text = re.sub(r'[^\x20-\x7E\u00A0-\uFFFF]', ' ', str(text))
        return re.sub(r'\s+', ' ', text).strip()
    except: return ""

def format_rakam(rakam_int):
    if rakam_int is None: return None
    try: return f"{int(rakam_int):,}".replace(",", ".")
    except: return None

def format_tarih_iso_v25(tarih_str, is_end_date=False):
    if not tarih_str: return None, None
    tarih_str = re.sub(r"['’`´](?:e|a|ye|ya|'de|'da|’de|’da)", "", tarih_str.lower().strip())
    aylar = {'ocak': '01', 'şubat': '02', 'mart': '03', 'nisan': '04', 'mayıs': '05', 'haziran': '06',
             'temmuz': '07', 'ağustos': '08', 'eylül': '09', 'ekim': '10', 'kasım': '11', 'aralık': '12'}
    
    try:
        parcalar = re.split(r'\s+', tarih_str)
        if len(parcalar) < 2: return None, None
        
        gun_str = ''.join(filter(str.isdigit, parcalar[0])).zfill(2)
        ay_adi = next((m for m in aylar if m in tarih_str), None)
        if not ay_adi: return None, None
        ay_num = aylar[ay_adi]
        
        yil_str = str(datetime.now().year)
        for p in parcalar:
            if p.isdigit() and len(p) == 4:
                yil_str = p
                break
                
        if is_end_date:
            iso_str = f"{yil_str}-{ay_num}-{gun_str}T23:59:59Z"
        else:
            iso_str = f"{yil_str}-{ay_num}-{gun_str}T00:00:00Z"
            
        return iso_str
    except: return None

def tahmin_et_kategori(text):
    text = text.lower()
    if re.search(r'akaryakıt|benzin|shell|opet|bp|petrol ofisi|total|aytemiz', text): return 'Yakıt'
    if re.search(r'market|migros|carrefour|a101|şok|bim|gıda|alışveriş', text): return 'Market'
    if re.search(r'restoran|yemek|cafe|burger|pizza|starbucks|yeme-içme', text): return 'Restoran & Kafe'
    if re.search(r'elektronik|teknoloji|mediamarkt|teknosa|vatan|beyaz eşya', text): return 'Elektronik'
    if re.search(r'giyim|moda|ayakkabı|lcwaikiki|defacto|beymen|boyner|zara|mavi', text): return 'Giyim & Moda'
    if re.search(r'trendyol|hepsiburada|amazon|n11|pazarama|e-ticaret|internet', text): return 'Online Alışveriş'
    if re.search(r'seyahat|otel|tatil|uçak|jolly|ets|setur|turizm', text): return 'Seyahat'
    if re.search(r'mtv|vergi|fatura|sgk|eğitim|okul|belediye', text): return 'Kamu & Vergi'
    if re.search(r'mobilya|yatak|ikea|evidea|koçtaş|yapı market', text): return 'Ev & Yaşam'
    return 'Diğer'

# --- 3. GELİŞMİŞ HESAPLAMA MOTORU (V13) ---

def extract_money(text):
    """Metinden para değerlerini (TL) çeker, YIL bilgilerini (2025 vb.) filtreler."""
    text = text.lower().replace('.', '').replace(',', '.')
    # Yılları temizle (2023-2029 arası)
    text = re.sub(r'202[3-9]', ' ', text)
    
    # Rakamları bul
    # Örn: 1000 tl, 1000tl, 1000
    matches = re.findall(r'(\d+)\s*(?:tl|try)?', text)
    values = []
    for m in matches:
        try:
            val = int(float(m))
            # Mantık filtresi: 10 TL altı (taksit sayısı olabilir) ve 5 Milyon TL üstü hariç
            if 10 < val < 5000000: 
                values.append(val)
        except: pass
    return values

def calculate_financials_v13(title, desc, full_text):
    """
    V13 Hesaplama Mantığı:
    1. Önce Maksimum Kazancı (Max Bonus) kesinleştir.
    2. Bu kazanca ulaşmak için gereken harcamayı (Target Spend) bul.
    """
    
    combined_text = f"{title} {desc} {full_text}".lower()
    # Temizlik: Noktaları binlik ayracı olarak kaldır, yılları sil
    clean_text = combined_text.replace('.', '').replace(',', '.')
    clean_text = re.sub(r'202[3-9]', '', clean_text) # Yılları uçur (2025 -> '')

    min_spend = 0
    max_earn = 0
    earning_str = None
    discount_str = None
    discount_perc = None

    # --- A. MAX KAZANÇ TESPİTİ ---
    # "Toplamda 500 TL", "En fazla 1.000 TL", "1.500 TL bonus"
    # Önce "toplam/en fazla" ifadelerine bak
    potential_max_rewards = []
    
    # Regex 1: "toplam/en fazla ... X TL ... bonus/puan/indirim"
    matches_max = re.findall(r'(?:toplam|en fazla|maksimum|kazanabileceğiniz)\s*.*?(\d+)\s*(?:tl)?\s*(?:bonus|puan|indirim)', clean_text)
    for m in matches_max:
        try: potential_max_rewards.append(int(m))
        except: pass

    # Regex 2: Başlıktaki net bonus ifadesi (Örn: "1.000 TL Bonus")
    title_clean = title.lower().replace('.', '').replace(',', '.')
    matches_title = re.findall(r'(\d+)\s*(?:tl)?\s*bonus', title_clean)
    for m in matches_title:
        try: potential_max_rewards.append(int(m))
        except: pass
        
    if potential_max_rewards:
        max_earn = max(potential_max_rewards)
    
    # Eğer hala 0 ise description'dan bulmaya çalış
    if max_earn == 0:
        desc_clean = desc.lower().replace('.', '').replace(',', '.')
        matches_desc = re.findall(r'(\d+)\s*(?:tl)?\s*bonus', desc_clean)
        if matches_desc:
             max_earn = max([int(x) for x in matches_desc])

    # --- B. HARCAMA (TARGET SPEND) TESPİTİ ---
    
    spend_found = False

    # Senaryo 1: Kademeli (Tiered) - "50.000 TL'ye 1.200 TL Bonus"
    # En yüksek ödülü veren harcamayı bulmaya çalışırız.
    if max_earn > 0:
        # (Harcama) ... (Ödül) ikililerini bul
        # Örn: "10000 tl ... 500 tl bonus"
        tiers = re.findall(r'(\d+)\s*tl.*?(\d+)\s*tl\s*(?:bonus|puan|indirim)', clean_text)
        best_spend_for_max = 0
        
        for s_str, e_str in tiers:
            spend = int(s_str)
            earn = int(e_str)
            # Eğer bu kademenin ödülü, bulduğumuz Max ödüle eşit veya çok yakınsa
            if earn >= max_earn * 0.9: 
                if spend > best_spend_for_max:
                    best_spend_for_max = spend
        
        if best_spend_for_max > 0:
            min_spend = best_spend_for_max
            spend_found = True

    # Senaryo 2: Döngüsel (Recurring) - "Her 2.500 TL'ye 130 TL"
    # Bu senaryoda Max Ödül'e ulaşmak için kaç tur gerektiğini hesaplarız.
    if not spend_found and "her" in clean_text and max_earn > 0:
        # "her ... X TL ... Y TL bonus"
        cycle_matches = re.findall(r'her\s*(\d+)\s*tl.*?(\d+)\s*tl\s*(?:bonus|puan)', clean_text)
        for s_str, e_str in cycle_matches:
            spend_unit = int(s_str)
            earn_unit = int(e_str)
            
            if earn_unit > 0:
                required_steps = math.ceil(max_earn / earn_unit)
                calculated_spend = required_steps * spend_unit
                # Mantık kontrolü: Harcama bonusun en az 2 katı olmalı (genelde %50'den fazla bonus vermezler)
                if calculated_spend >= max_earn * 2:
                    min_spend = calculated_spend
                    spend_found = True
                    break

    # Senaryo 3: Yüzde (%) - "%10 Bonus... En fazla 500 TL"
    if not spend_found and max_earn > 0:
        perc_match = re.search(r'%\s*(\d+)', clean_text)
        if perc_match:
            rate = int(perc_match.group(1))
            discount_perc = rate
            discount_str = f"%{rate}"
            if rate > 0:
                # 500 / 0.10 = 5000
                calculated_spend = int(max_earn / (rate / 100))
                min_spend = calculated_spend
                spend_found = True

    # Senaryo 4: Düz Giriş Limiti (Fallback) - "1.000 TL ve üzeri"
    # Eğer yukarıdakiler çalışmadıysa, metindeki en büyük mantıklı harcama tutarını al
    if not spend_found:
        # "X TL ve üzeri" geçen sayıları al
        limits = re.findall(r'(\d+)\s*tl.*?üzeri', clean_text)
        valid_limits = []
        for l in limits:
            val = int(l)
            # Yıl (2025) ile karışmaması için kontrol, zaten text clean'de sildik ama 
            # 2000-2030 aralığına dikkat. Genelde harcama limitleri yuvarlaktır.
            if val > 50: 
                valid_limits.append(val)
        
        if valid_limits:
            if max_earn > 500: 
                # Eğer ödül büyükse, muhtemelen en yüksek limiti istiyorlardır
                min_spend = max(valid_limits)
            else:
                # Ödül küçükse, giriş limitini al
                min_spend = min(valid_limits)

    # String Formatlama
    if max_earn > 0:
        earning_str = f"{format_rakam(max_earn)} TL Bonus"
    elif discount_str:
        earning_str = f"{discount_str} İndirim"
    else:
        taksit_match = re.search(r'(\d+)\s*taksit', clean_text)
        if taksit_match:
            earning_str = f"{taksit_match.group(1)} Taksit"
            discount_str = f"{taksit_match.group(1)} Taksit"

    return min_spend, earning_str, discount_str, discount_perc, max_earn

# --- 4. DİĞER AYRIŞTIRICILAR ---

def extract_cards_final(soup):
    full_text = soup.get_text()
    card_patterns = [
        (r'bonus\s+genç', "Bonus Genç"),
        (r'bonus\s+flexi', "Bonus Flexi"),
        (r'money\s+bonus', "Money Bonus"),
        (r'bonus\s+business', "Bonus Business"),
        (r'miles', "Miles&Smiles Garanti BBVA"),
        (r'shop', "Shop&Fly"),
        (r'american', "American Express"),
        (r'paracard', "Paracard"),
        (r'flexi', "Flexi"),
        (r'easy', "Easy"),
        (r'troy', "Troy Logolu Kartlar"),
        (r'bonus\s+platinum', "Bonus Platinum"),
        (r'bonus\s+gold', "Bonus Gold"),
        (r'garanti\s+bonus', "Garanti Bonus")
    ]
    
    found_cards = []
    text_lower = full_text.lower()
    # "Dahil değildir" kısmını atıp pozitif metinde ara
    text_positive = re.split(r'dahil\s+değil', text_lower)[0]
    
    for pattern, name in card_patterns:
        if re.search(pattern, text_positive):
            if name not in found_cards:
                found_cards.append(name)
    
    if not found_cards:
        found_cards = ["Garanti Bonus"]
    return found_cards

def extract_participation_final(soup):
    method = "Detayları kontrol ediniz."
    points = []
    text = soup.get_text()
    
    sms_match = re.search(r'([A-ZİÖÜŞĞÇ0-9]{3,15})\s*(?:yazıp|yaz)\s*,?\s*(?:3340)', text, re.IGNORECASE)
    sms_text = ""
    if sms_match:
        keyword = sms_match.group(1).upper().strip()
        if keyword not in ["BONUS", "HEMEN", "KAMPANYA"]:
            sms_text = f"SMS ({keyword} -> 3340)"
            points.append(f"{keyword} yazıp 3340'a SMS gönderiniz.")
            
    has_app = "BonusFlaş" in text or "Hemen Katıl" in text
    
    if has_app and sms_text:
        method = f"BonusFlaş veya {sms_text}"
        points.insert(0, "BonusFlaş uygulamasından 'Hemen Katıl' butonuna tıklayınız.")
    elif has_app:
        method = "BonusFlaş Uygulaması"
        points.append("BonusFlaş uygulamasından 'Hemen Katıl' butonuna tıklayınız.")
    elif sms_text:
        method = sms_text
        
    if "otomatik" in text.lower() and not sms_text and not has_app:
        method = "Otomatik Katılım"
        points = ["Kampanyaya katılım otomatiktir."]
        
    return method, points

# --- 5. ANA PARSER ---

def parse_campaign_v13(soup, url, c_id):
    title_elm = soup.select_one('.campaign-detail-title h1')
    title = temizle_metin(title_elm.get_text()) if title_elm else "Başlık Bulunamadı"
    
    img_elm = soup.select_one('.campaign-detail__image img')
    image_url = urljoin(BASE_URL, img_elm['src']) if img_elm else None
    
    date_elm = soup.select_one('.campaign-date')
    date_text = temizle_metin(date_elm.get_text()) if date_elm else ""
    
    # Tarih
    parts = date_text.split('-')
    valid_from = None
    valid_until = None
    if len(parts) > 0:
        valid_from = format_tarih_iso_v25(parts[0].strip(), is_end_date=False)
    if len(parts) > 1:
        valid_until = format_tarih_iso_v25(parts[-1].strip(), is_end_date=True)
    elif len(parts) == 1 and valid_from:
        valid_until = format_tarih_iso_v25(parts[0].strip(), is_end_date=True)
        valid_from = None 

    desc = title
    how_win_header = soup.find('h2', string=re.compile('NASIL KAZANIRIM', re.IGNORECASE))
    if how_win_header:
        desc_p = how_win_header.find_next_sibling('p')
        if desc_p: desc = temizle_metin(desc_p.get_text())

    # Metni birleştir (Başlık + Açıklama + Detaylar)
    full_text_raw = soup.get_text(separator=' ')
    
    # --- HESAPLAMA MOTORUNU ÇALIŞTIR ---
    min_spend, earning, discount, discount_perc, max_earn = calculate_financials_v13(title, desc, full_text_raw)
    
    eligible_cards = extract_cards_final(soup)
    part_method, part_points = extract_participation_final(soup)
    
    conditions = []
    detail_list = soup.select('.how-to-win ul.disc li')
    for li in detail_list:
        txt = temizle_metin(li.get_text())
        if txt and len(txt) > 15:
            conditions.append(txt)

    category = tahmin_et_kategori(title + " " + desc)
    
    difficulty = "Kolay"
    if "SMS" in part_method or "BonusFlaş" in part_method: difficulty = "Orta"
    if min_spend > 5000: difficulty = "Zor"

    return {
        "id": c_id,
        "title": title,
        "description": desc,
        "provider": IMPORT_SOURCE_NAME,
        "category": category,
        "url": url,
        "image": image_url,
        "images": [image_url] if image_url else [],
        "discount": discount,
        "earning": earning,
        "min_spend": min_spend,
        "max_discount": max_earn,
        "discount_percentage": discount_perc,
        "valid_from": valid_from,
        "valid_until": valid_until,
        "participation_method": part_method,
        "participation_points": part_points,
        "conditions": conditions[:30],
        "eligible_customers": eligible_cards,
        "difficulty_level": difficulty,
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_url": BASE_URL
    }

def get_campaign_list(session):
    print("Kampanya linkleri taranıyor...")
    links = []
    try:
        resp = session.get(CAMPAIGN_LIST_URL, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(resp.content, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/kampanyalar/' in href and len(href.split('/')) > 2:
                if not any(x in href for x in ['sektor', 'kategori', 'marka', '#', 'javascript']):
                    full = urljoin(BASE_URL, href)
                    if full not in links: links.append(full)
    except Exception as e:
        print(f"Liste hatası: {e}")
    return links

if __name__ == "__main__":
    print(f"Garanti Bonus Scraper V13 (Fixed Math Logic) Başlatılıyor...")
    all_data = []
    with requests.Session() as s:
        urls = get_campaign_list(s)
        if len(urls) > CAMPAIGN_LIMIT: urls = urls[:CAMPAIGN_LIMIT]
        
        print(f"Toplam {len(urls)} kampanya işlenecek...")
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] İşleniyor: {url}")
            try:
                resp = s.get(url, headers=HEADERS, timeout=15)
                soup = BeautifulSoup(resp.content, 'html.parser')
                data = parse_campaign_v13(soup, url, i)
                if data: 
                    all_data.append(data)
                    # Kontrol Çıktısı
                    print(f"   -> Spend: {data['min_spend']}, Max Earn: {data['max_discount']}")
            except Exception as e:
                print(f"Hata: {e}")
            time.sleep(random.uniform(0.5, 1.2))
            
    if all_data:
        with open(JSON_FILE_NAME, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)
        print(f"🎉 İşlem Tamamlandı: {JSON_FILE_NAME}")
