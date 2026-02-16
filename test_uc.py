import undetected_chromedriver as uc
import time

print("Testing undetected_chromedriver launch...")
try:
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    print("Initializing Chrome...")
    driver = uc.Chrome(options=options)
    
    print("✅ Chrome launched!")
    driver.get("https://www.maximum.com.tr")
    print(f"Title: {driver.title}")
    
    time.sleep(5)
    driver.quit()
    print("✅ Test done")
except Exception as e:
    print(f"❌ Failed: {e}")
