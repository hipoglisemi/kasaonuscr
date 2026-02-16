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
OUTPUT_FILE = "vakifbank_parallel_final.json"
IMPORT_SOURCE_NAME = "VakıfBank World"
WORKER_COUNT = 4  # Aynı anda çalışacak tarayıcı sayısı (Bilgisayarın gücüne göre artırılabilir)

# --- YARDIMCI FONKSİYONLAR (Ziraat v31 Motoru) ---
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
    if any(x in t for x in ["trendyol","amazon","hepsiburada","n11","pazarama"]): return "Online Alışveriş"
    if "akaryakıt" in t or "benzin" in t: return "Yakıt"
    if "market" in t or "gıda" in t: return "Market"
    if "restoran" in t or "kafe" in t: return "Restoran & Kafe"
    if "giyim" in t or "moda" in t: return "Giyim & Moda"
    if "elektronik" in t or "teknoloji" in t: return "Elektronik"
    if "mobilya" in t: return "Ev & Yaşam"
    if "seyahat" in t or "uçak" in t or "otel" in t: return "Seyahat"
    return "Diğer"

def extract_financials(text, title):
    t_low = tr_lower(text.replace('.', '').replace(',', '.'))
    title_low = tr_lower(title)
    min_s, max_d, earn, disc = 0, 0, None, None
    
    # Taksit
    if "taksit" in title_low:
        tm = re.findall(r'(\d+)\s*taksit', t_low)
        if tm:
            disc = f"{max(map(int, tm))} Taksit"
            ms = re.search(r'(\d+)\s*tl.*?taksit', t_low)
            if ms: min_s = int(ms.group(1))
        return min_s, None, disc, 0, 0

    # Toplam
    mt = re.search(r'toplam(?:da)?\s*(\d+)\s*(?:tl|worldpuan)', t_low)
    if mt: max_d = int(mt.group(1))

    # Döngüsel
    mc = re.search(r'her\s*(\d+)\s*tl.*?(\d+)\s*tl', t_low)
    if mc:
        min_s = int(mc.group(1)); unit = int(mc.group(2))
        earn = f"{format_rakam(max_d if max_d else unit)} TL Worldpuan"
        return min_s, earn, None, 0, max_d
    
    # Tek seferlik
    mo = re.search(r'(\d+)\s*tl.*?(\d+)\s*tl\s*(?:worldpuan|indirim)', t_low)
    if mo:
        min_s = int(mo.group(1)); val = int(mo.group(2))
        if val != min_s:
            suff = "İndirim" if "indirim" in t_low else "Worldpuan"
            earn = f"{format_rakam(val)} TL {suff}"
            if not max_d: max_d = val

    return min_s, earn, disc, 0, max_d

def extract_cards(text):
    cards = []
    t = tr_lower(text)
    if "ticari" in t or "business" in t: cards.append("VakıfBank Ticari")
    if "bankomat" in t: cards.append("Bankomat Kart")
    if "worldcard" in t or "bireysel" in t: cards.append("VakıfBank Worldcard")
    if "platinum" in t: cards.append("Platinum")
    if "rail&miles" in t: cards.append("Rail&Miles")
    if not cards: cards.append("VakıfBank Kartları")
    return list(set(cards))

# --- ÇALIŞAN FONKSİYONU (WORKER) ---
def worker_task(urls, worker_id):
    """Bu fonksiyon ayrı bir tarayıcıda çalışır ve kendine verilen URL listesini işler."""
    print(f"   🤖 İşçi #{worker_id} başladı. ({len(urls)} kampanya işleyecek)")
    
    chrome_options = Options()
    # Hız için resimleri yükleme ve Eager modunu kullan
    chrome_options.add_argument("--headless=new") # Arka planda çalışsın (Hızlı)
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
                # Başlığın gelmesini bekle (Max 5 sn)
                try:
                    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1")))
                except: pass # Devam et

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Veri Çekme
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
                
                # Analiz
                vf, vu = extract_dates(full_text)
                cat = get_category(full_text, title)
                min_s, earn, disc, _, max_d = extract_financials(full_text, title)
                cards = extract_cards(full_text)
                
                part = []
                if "cepte kazan" in tr_lower(full_text): part.append("Cepte Kazan")
                if "sms" in tr_lower(full_text): part.append("SMS")
                part_str = ", ".join(part) if part else "Otomatik / Detaylara bakın"
                
                desc = conditions[0] if conditions else title
                if len(desc) > 300: desc = desc[:300] + "..."

                item = {
                    "id": 0, # Sonra güncellenecek
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
        print(f"   ✅ İşçi #{worker_id} görevini tamamladı.")
        
    return results

# --- ANA FONKSİYON ---
def main():
    print(f"🚀 {IMPORT_SOURCE_NAME} Hızlı Tarayıcı Başlıyor...")
    
    # 1. ADIM: Linkleri Topla (Tek Tarayıcı ile Hızlıca)
    print("\n📋 Adım 1: Kampanya Linkleri Toplanıyor...")
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

    # 2. ADIM: İş Bölümü ve Paralel Çalıştırma
    print(f"\n⚡ Adım 2: {len(campaign_urls)} kampanya {WORKER_COUNT} işçiye bölüştürülüyor...")
    
    # URL listesini işçi sayısına böl
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
    for i, item in enumerate(final_data, 1):
        item['id'] = i
        
    if final_data:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=4)
        print(f"\n🎉 İŞLEM BİTTİ! {len(final_data)} kampanya '{OUTPUT_FILE}' dosyasına kaydedildi.")
    else:
        print("\n❌ Veri çekilemedi.")

if __name__ == "__main__":
    main()