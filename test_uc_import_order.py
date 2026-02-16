from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
import time

print("Testing undetected_chromedriver with prior selenium import...")

try:
    print("Using Selenium Options first (simulating scraper structure)...")
    sel_options = Options()
    
    print("Now initializing UC...")
    uc_options = uc.ChromeOptions()
    uc_options.add_argument('--no-sandbox')
    uc_options.add_argument('--disable-dev-shm-usage')
    
    driver = uc.Chrome(options=uc_options)
    
    print("✅ Chrome launched!")
    driver.get("https://www.maximum.com.tr")
    print(f"Title: {driver.title}")
    
    time.sleep(2)
    driver.quit()
    print("✅ Test done")
except Exception as e:
    print(f"❌ Failed: {e}")
