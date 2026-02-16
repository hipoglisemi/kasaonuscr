from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import shutil

print("Testing webdriver-manager installation...")

try:
    # Try to install the driver
    print("Trying to install driver...")
    driver_path = ChromeDriverManager().install()
    print(f"✅ Driver installed at: {driver_path}")
    
    # Try to connect to localhost:9222
    print("Trying to connect to Chrome at localhost:9222...")
    options = Options()
    options.debugger_address = "localhost:9222"
    service = Service(executable_path=driver_path)
    
    driver = webdriver.Chrome(service=service, options=options)
    print("✅ Connected successfully!")
    print(f"Title: {driver.title}")
    
    driver.quit()
    
except Exception as e:
    print(f"❌ Failed: {e}")
