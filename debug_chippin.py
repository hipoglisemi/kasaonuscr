import undetected_chromedriver as uc
import time
from selenium.webdriver.common.by import By

def debug_chippin():
    print("Initializing Driver (Undetected, Headless=False)...")
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1")
    # options.add_argument("--headless")
    
    driver = None
    try:
        driver = uc.Chrome(options=options)
        url = "https://www.chippin.com.tr"
        print(f"Navigating to Home: {url}...")
        driver.get(url)
        time.sleep(10)
        
        # Check for Privacy Error (in case it happens on hoempage)
        if "Gizlilik hatası" in driver.title or "Privacy error" in driver.title:
            try:
                driver.execute_script('document.getElementById("details-button").click();')
                time.sleep(1)
                driver.execute_script('document.getElementById("proceed-link").click();')
            except: pass
        
        print("Looking for /kampanyalar link...")
        # Try to find link by href
        links = driver.find_elements(By.XPATH, "//a[contains(@href, '/kampanyalar')]")
        if links:
            print(f"Clicking campaign link: {links[0].get_attribute('href')}")
            links[0].click()
            time.sleep(10)
        else:
            print("❌ Campaign link not found on homepage.")

        # Check dump
        
        print("Saving screenshot...")
        driver.save_screenshot("chippin_debug_uc.png")
        
        print("Saving HTML...")
        with open("chippin_dump_uc.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
            
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_chippin()
