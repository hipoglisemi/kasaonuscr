
import undetected_chromedriver as uc
import time

print("Start")
try:
    options = uc.ChromeOptions()
    # options.add_argument('--headless') 
    driver = uc.Chrome(options=options)
    print("Driver created")
    driver.get("https://google.com")
    print(driver.title)
    time.sleep(2)
    driver.quit()
    print("Done")
except Exception as e:
    print(f"Error: {e}")
