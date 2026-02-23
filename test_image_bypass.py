import undetected_chromedriver as uc
import time
import requests
import base64
from selenium.webdriver.common.by import By

def test_bypass():
    print("🚀 Starting Selenium for Cookie Bypass...")
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--headless") # Keep headful to pass WAF verification
    
    driver = uc.Chrome(options=options)
    
    try:
        url = "https://www.chippin.com.tr"
        print(f"   🌐 Navigating to {url}...")
        driver.get(url)
        time.sleep(5)
        
        # Privacy Error Bypass
        if "Gizlilik hatası" in driver.title or "Privacy error" in driver.title:
            print("   🚨 Privacy Error detected! Trying to bypass...")
            try:
                driver.execute_script('document.getElementById("details-button").click();')
                time.sleep(1)
                driver.execute_script('document.getElementById("proceed-link").click();')
                print("   ✅ Clicked Proceed Link.")
                time.sleep(5)
            except Exception as e:
                print(f"   Bypass failed: {e}")

        # Get Cookies
        selenium_cookies = driver.get_cookies()
        print(f"   🍪 Got {len(selenium_cookies)} cookies.")
        
        # Setup Requests Session
        session = requests.Session()
        for cookie in selenium_cookies:
            session.cookies.set(cookie['name'], cookie['value'])
            
        session.headers.update({
            "User-Agent": driver.execute_script("return navigator.userAgent;"),
            "Referer": "https://www.chippin.com.tr/kampanyalar"
        })
        
        # Verify Session with Image
        img_url = "https://www.chippin.com.tr/campaign/banner/Arcelikte_her_odemede_3_ChipPuan_35.000_TL_ve_uzerine_toplamda_3.750_TLye_varan_Puan_hediye_12122025_508_banner.png"
        print(f"   ⬇️ Downloading Image: {img_url}")
        
        r = session.get(img_url, verify=False, timeout=10)
        print(f"   Status: {r.status_code}")
        print(f"   Content-Type: {r.headers.get('Content-Type')}")
        
        if r.status_code == 200 and "image" in r.headers.get("Content-Type", ""):
            print("   ✅ SUCCESS! Image downloaded.")
            with open("test_bypass_img.png", "wb") as f:
                f.write(r.content)
            print("   💾 Saved to test_bypass_img.png")
        else:
            print("   ❌ Failed.")
            print(r.text[:500])

    except Exception as e:
        print(f"   ❌ Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_bypass()
