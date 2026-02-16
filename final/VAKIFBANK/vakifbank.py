import time
import json
import re
import math
import random
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

# --- GEREKLİ KÜTÜPHANELER ---
# pip3 install selenium webdriver-manager requests beautifulsoup4
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- AYARLAR ---
BASE_URL = "https://www.vakifkart.com.tr"
LIST_URL_TEMPLATE = "https://www.vakifkart.com.tr/kampanyalar/sayfa/{}"
OUTPUT_FILE = "vakifbank_kampanyalar_v37_ultimate.json"
IMPORT_SOURCE_NAME = "VakıfBank World"
WORKER_COUNT = 4  # Aynı anda çalışacak tarayıcı sayısı

# --- YARDIMCI FONKSİYONLAR ---

def tr_lower(text):
    return text.replace('I', 'ı').replace('İ', 'i').lower()

def temizle_metin(text):
    if not text: return ""
    text = text.replace('\n', ' ').replace('\r', '')
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'^(Sektör:|Kampanya Koşulları:|Kampanya Detayları:)\s*', '', text, flags=re.IGNORECASE)
    return text.strip(' ,.:;-')

def format_rakam(rakam_int):
    if rakam_int is None: return None
    try: return f"{int(rakam_int):,}".replace(",", ".")
    except: return None

def text_to_int_tr_max(text):
    text = tr_lower(text)
    mapping = {'birinci': 1, 'ilk': 1, 'ikinci': 2, 'üçüncü': 3, 'dördüncü': 4, 'beşinci': 5, 'altıncı': 6}
    found = [v for k, v in mapping.items() if k in text]
    matches = re.findall(r'(\d+)\.\s*(?:işlem|harcama|alışveriş)', text)
    found.extend([int(m) for m in matches])
    return max(found) if found else None

def format_tarih_iso(tarih_str, is_end=False):
    if not tarih_str: return None
    ts = tr_lower(tarih_str)
    aylar = {'ocak':'01','şubat':'02','mart':'03','nisan':'04','mayıs':'05','haziran':'06',
             'temmuz':'07','ağustos':'08','eylül':'09','ekim':'10','kasım':'11','aralık':'12'}
    try:
        m = re.search(r'(\d{1,2})\s*-\s*(\d{1,2})\s*([a-zğüşıöç]+)\s*(\d{4})', ts)
        if m:
            g1, g2, ay, yil = m.groups()
            g = g2 if is_end else g1
            h = "23:59:59" if is_end else "00:00:00"
            return f"{yil}-{aylar.get(ay,'01')}-{str(g).zfill(2)}T{h}Z"
        m2 = re.search(r'(\d{1,2})\s*([a-zğüşıöç]+)\s*-\s*(\d{1,2})\s*([a-zğüşıöç]+)\s*(\d{4})', ts)
        if m2:
            g1, a1, g2, a2, yil = m2.groups()
            if is_end: return f"{yil}-{aylar.get(a2,'12')}-{str(g2).zfill(2)}T23:59:59Z"
            return f"{yil}-{aylar.get(a1,'01')}-{str(g1).zfill(2)}T00:00:00Z"
        return None
    except: return None

def extract_dates(text): return format_tarih_iso(text, False), format_tarih_iso(text, True)

def get_category(text, title):
    t = tr_lower(title + " " + text)
    if any(x in t for x in ["trendyol","amazon","hepsiburada","n11","pazarama","e-ticaret"]): return "Online Alışveriş"
    if "akaryakıt" in t or "benzin" in t: return "Yakıt"
    if "market" in t or "gıda" in t: return "Market"
    if "restoran" in t or "kafe" in t: return "Restoran & Kafe"
    if "giyim" in t or "moda" in t: return "Giyim & Moda"
    if "elektronik" in t or "teknoloji" in t: return "Elektronik"
    if "mobilya" in t: return "Ev & Yaşam"
    if "seyahat" in t or "uçak" in t or "otel" in t: return "Seyahat"
    if "eğitim" in t: return "Eğitim"
    return "Diğer"

# --- V37 MATEMATİK MOTORU ---
def extract_financials_v37(text, title):
    # Rakam temizliği
    text_clean = re.sub(r'(?<=\d)\.(?=\d)', '', text) 
    t_low = tr_lower(text_clean.replace(',', '.'))
    title_low = tr_lower(title)
    
    min_s, max_d, earn, disc = 0, 0, None, None
    
    # 1. Taksit / Erteleme Kalkanı
    if any(x in title_low for x in ["taksit", "erteleme", "faizsiz"]):
        tm = re.findall(r'(\d+)\s*taksit', t_low)
        if tm:
            disc = f"{max(map(int, tm))} Taksit"
            ms = re.search(r'(\d+)\s*tl.*?taksit', t_low)
            if ms: min_s = int(ms.group(1))
        
        # "Puan", "İndirim" yoksa earning'i kesinlikle boş bırak
        if not re.search(r'worldpuan|indirim|puan|hediye|kazan', t_low):
            return min_s, None, disc, 0, 0

    # 2. Toplam Ödül
    mt = re.search(r'toplam(?:da)?\s*(\d+)\s*(?:tl|worldpuan|indirim)', t_low)
    if mt: max_d = int(mt.group(1))

    # 3. Döngüsel Hesap (Her X TL... Toplam Y TL)
    mc = re.search(r'her\s*(\d+)\s*tl.*?(\d+)\s*tl', t_low)
    if mc:
        unit_spend = int(mc.group(1))
        unit_earn = int(mc.group(2))
        
        suffix = "İndirim" if "indirim" in t_low else "Worldpuan"
        
        if max_d > 0 and unit_earn > 0:
            count = max_d / unit_earn
            min_s = int(count * unit_spend) # Örn: 4 * 5000 = 20000 TL
            earn = f"{format_rakam(max_d)} TL {suffix}"
        else:
            min_s = unit_spend
            earn = f"{format_rakam(unit_earn)} TL {suffix}"
            
        return min_s, earn, None, 0, max_d
    
    # 4. Yüzdesel
    mp = re.search(r'%\s*(\d+)', t_low)
    if mp:
        perc = int(mp.group(1))
        suffix = "İndirim" if "indirim" in t_low else "Worldpuan"
        
        ms = re.search(r'(\d+)\s*tl\s*(?:ve üzeri|üzeri)', t_low)
        if ms: min_s = int(ms.group(1))
        
        if max_d > 0:
            earn = f"{format_rakam(max_d)} TL {suffix}"
            if perc > 0: min_s = int(max_d * 100 / perc)
        else:
            earn = f"%{perc} {suffix}"
            
        return min_s, earn, disc, perc, max_d

    # 5. Tek Seferlik / Ek Kart / Sözüne
    # Ek Kart veya Sözüne durumlarını yakala
    mo = re.search(r'(\d+)\s*tl.*?(\d+)\s*tl\s*(?:worldpuan|ekstre indirimi|indirim|kazan)', t_low)
    if mo:
        m_val = int(mo.group(1)); r_val = int(mo.group(2))
        # Ödül harcamaya eşit değilse (1000 harca 1000 kazan mantıksız değilse)
        if r_val != m_val: 
            suffix = "İndirim" if "indirim" in t_low else "Worldpuan"
            earn = f"{format_rakam(r_val)} TL {suffix}"
            min_s = m_val
            if not max_d: max_d = r_val
    
    # Ek Kart Özel Kontrolü (ID 30 gibi)
    if "ek kart" in title_low and not earn:
         match_ek = re.search(r'(\d+)\s*tl\s*worldpuan', t_low)
         if match_ek:
             earn = f"{match_ek.group(1)} TL Worldpuan"
             max_d = int(match_ek.group(1))

    return min_s, earn, disc, 0, max_d

def extract_cards(text):
    cards = []
    t = tr_lower(text)
    
    # Pozitif
    if "ticari" in t or "business" in t: cards.append("VakıfBank Ticari")
    if "bankomat" in t: cards.append("Bankomat Kart")
    if "worldcard" in t or "bireysel" in t: cards.append("VakıfBank Worldcard")
    if "platinum" in t: cards.append("Platinum")
    if "rail&miles" in t: cards.append("Rail&Miles")
    if "troy" in t: cards.append("TROY Logolu")
    if not cards: cards.append("VakıfBank Kartları")
    
    # Negatif Filtre (Dahil Değildir)
    if "dahil değildir" in t or "geçerli değildir" in t:
        sentences = t.split('.')
        for sent in sentences:
            if "dahil değildir" in sent or "geçerli değildir" in sent:
                if "ticari" in sent and "VakıfBank Ticari" in cards: cards.remove("VakıfBank Ticari")
                if "bankomat" in sent and "Bankomat Kart" in cards: cards.remove("Bankomat Kart")
                if "business" in sent and "VakıfBank Ticari" in cards: cards.remove("VakıfBank Ticari")

    return list(set(cards))

def extract_participation_v37(text):
    """SMS kodunu ve son 6 hane detayını yakalar."""
    methods = []
    t_low = tr_lower(text)
    
    if "cepte kazan" in t_low: methods.append("Cepte Kazan")
    
    if "sms" in t_low:
        # Kod yakala: "EKGIDA yazıp..."
        match_code = re.search(r'([a-z0-9]{3,})\s*yazıp', t_low)
        code = match_code.group(1).upper() if match_code else ""
        
        # Son 6 hane detayı var mı?
        if "son 6" in t_low or "son altı" in t_low:
            if code: methods.append(f"SMS ({code} boşluk kartın son 6 hanesi -> 5724)")
            else: methods.append("SMS (Kartın son 6 hanesi ile)")
        elif code:
            methods.append(f"SMS ({code} -> 5724)")
        else:
            methods.append("SMS")

    if "otomatik" in t_low: return "Otomatik Katılım"
    
    return ", ".join(methods) if methods else "Otomatik / Detaylara bakın"


# --- ÇALIŞAN FONKSİYONU (WORKER) ---
def worker_task(urls, worker_id):
    print(f"   🤖 İşçi #{worker_id} başladı. ({len(urls)} kampanya)")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.page_load_strategy = 'eager' 
    prefs = {"profile.managed_default_content_settings.images": 2} 
    chrome_options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    results = []
    
    try:
        for i, url in enumerate(urls):
            try:
                driver.get(url)
                try: WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1")))
                except: pass

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                title_el = soup.select_one('.kampanyaDetay .title h1') or soup.select_one('h1')
                title = temizle_metin(title_el.text) if title_el else "Başlık Yok"
                
                img_el = soup.select_one('.kampanyaDetay .coverSide img')
                image = urljoin(BASE_URL, img_el['src']) if img_el else None
                
                content_div = soup.select_one('.kampanyaDetay .contentSide')
                conditions = []
                full_text = ""
                
                if content_div:
                    lis = content_div.select('li')
                    if lis:
                        conditions = [temizle_metin(li.text) for li in lis]
                    else:
                        ps = content_div.select('p')
                        conditions = [temizle_metin(p.text) for p in ps if len(p.text) > 15]
                    full_text = " ".join(conditions)
                
                # v37 Analizleri
                vf, vu = extract_dates(full_text)
                cat = get_category(full_text, title)
                min_s, earn, disc, _, max_d = extract_financials_v37(full_text, title)
                cards = extract_cards(full_text)
                part_str = extract_participation_v37(full_text) # v37 SMS Format
                
                desc = conditions[0] if conditions else title
                if len(desc) > 300: desc = desc[:300] + "..."

                item = {
                    "id": 0, 
                    "title": title,
                    "provider": IMPORT_SOURCE_NAME,
                    "category": cat,
                    "merchant": None,
                    "image": image,
                    "images": [image] if image else [],
                    "description": desc,
                    "url": url,
                    "discount": disc,
                    "earning": earn,
                    "min_spend": min_s,
                    "max_discount": max_d,
                    "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "valid_from": vf,
                    "valid_until": vu,
                    "participation_method": part_str,
                    "conditions": conditions,
                    "eligible_customers": cards,
                    "source_url": BASE_URL
                }
                results.append(item)
                
            except Exception as e:
                print(f"      ! Hata (Worker {worker_id}): {e}")

    finally:
        driver.quit()
        print(f"   ✅ İşçi #{worker_id} tamamladı.")
        
    return results

# --- ANA FONKSİYON ---
def main():
    print(f"🚀 {IMPORT_SOURCE_NAME} Ultimate Scraper v37 (Mac Parallel)...")
    
    # 1. Linkleri Topla
    print("\n📋 Kampanya Linkleri Toplanıyor...")
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    campaign_urls = []
    try:
        for page in range(1, 15):
            url = LIST_URL_TEMPLATE.format(page)
            driver.get(url)
            time.sleep(1.5)
            
            items = driver.find_elements(By.CSS_SELECTOR, "div.mainKampanyalarDesktop:not(.eczk) .list a.item")
            if not items: break
                
            for item in items:
                href = item.get_attribute('href')
                if href and href not in campaign_urls:
                    campaign_urls.append(href)
            print(f"   -> Sayfa {page} tarandı. Toplam: {len(campaign_urls)}")
    finally:
        driver.quit()

    if not campaign_urls:
        print("❌ Link bulunamadı.")
        return

    # 2. Paralel Detay Çekimi
    print(f"\n⚡ {len(campaign_urls)} kampanya {WORKER_COUNT} işçiye bölüştürülüyor...")
    chunk_size = math.ceil(len(campaign_urls) / WORKER_COUNT)
    chunks = [campaign_urls[i:i + chunk_size] for i in range(0, len(campaign_urls), chunk_size)]
    
    final_data = []
    
    with ThreadPoolExecutor(max_workers=WORKER_COUNT) as executor:
        futures = []
        for i, chunk in enumerate(chunks):
            futures.append(executor.submit(worker_task, chunk, i+1))
        
        for future in futures:
            final_data.extend(future.result())

    # ID'leri düzenle ve Kaydet
    for i, item in enumerate(final_data, 1): item['id'] = i
        
    if final_data:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=4)
        print(f"\n🎉 İŞLEM BİTTİ! {len(final_data)} kampanya '{OUTPUT_FILE}' dosyasına kaydedildi.")
    else:
        print("\n❌ Veri çekilemedi.")

if __name__ == "__main__":
    main()