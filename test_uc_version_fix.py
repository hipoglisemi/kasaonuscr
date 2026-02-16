import undetected_chromedriver as uc
import time

print("Testing UC with version_main=144...")
try:
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = uc.Chrome(options=options, version_main=144)
    
    print("✅ Chrome launched!")
    driver.get("https://www.maximum.com.tr")
    print(f"Title: {driver.title}")
    
    time.sleep(2)
    driver.quit()
    print("✅ Test done")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"❌ Failed: {e}")
