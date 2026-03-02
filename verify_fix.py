import sys
import os
import re
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def clean(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', text).strip()

def test_logic(url):
    print(f"--- STARTING TEST FOR: {url} ---")
    with sync_playwright() as p:
        try:
            print("Connecting to browser...")
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            print("Connected to CDP successful.")
            context = browser.contexts[0] if len(browser.contexts) > 0 else browser.new_context()
        except Exception as e:
            print(f"CDP failed: {e}. Launching headless...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()

        page = context.new_page()
        print(f"Loading page...")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            print("Page loaded.")
            
            # Scroll to bottom
            print("Scrolling to bottom...")
            page.evaluate("""async () => {
                await new Promise((resolve) => {
                    let totalHeight = 0;
                    let distance = 400;
                    let timer = setInterval(() => {
                        let scrollHeight = document.body.scrollHeight;
                        window.scrollBy(0, distance);
                        totalHeight += distance;
                        if(totalHeight >= scrollHeight){
                            clearInterval(timer);
                            resolve();
                        }
                    }, 100);
                });
            }""")
            time.sleep(3)
            print("Scroll complete.")
            
            soup = BeautifulSoup(page.content(), "html.parser")
            
            # Content Extraction Logic
            content_parts = []
            containers = soup.select(".page-content, section div.container, .detail-text, .campaign-content, .text-area")
            
            print(f"Found {len(containers)} suspect containers.")
            
            for i, container in enumerate(containers):
                text = container.get_text(separator="\n", strip=True)
                if len(text) > 400 and "Ana Sayfa" not in text[:100]:
                    if not any(text[:100] in p for p in content_parts):
                        content_parts.append(text)
                        print(f"✅ Container {i} accepted (len {len(text)})")
                else:
                    reason = "too short" if len(text) <= 400 else "breadcrumb detected"
                    # print(f"❌ Container {i} rejected ({reason})")

            if not content_parts:
                print("Using fallback (sections)...")
                sections = soup.select("section")
                for s in sections:
                    t = s.get_text(separator="\n", strip=True)
                    if len(t) > 300 and "Üzgünüz" not in t:
                        content_parts.append(t)

            full_text = "\n\n".join(content_parts)
            print("\n" + "="*50)
            print(f"TOTAL EXTRACTED LENGTH: {len(full_text)}")
            if len(full_text) > 0:
                print("SAMPLE (First 500 chars):")
                print(full_text[:500])
                print("\nSAMPLE (Last 500 chars):")
                print(full_text[-500:])
            else:
                print("!!! NO CONTENT EXTRACTED !!!")
            print("="*50)
        except Exception as e:
            print(f"Error during test: {e}")
        finally:
            page.close()
            # If we launched, we should close. If we connected, maybe not?
            # browser.close()

if __name__ == "__main__":
    test_url = "https://www.maximiles.com.tr/kampanyalar/maximiles-black-ile-emiratesten-alacaginiz-ucak-biletlerinde-300-usdye-varan-indirim-ayricaligi"
    test_logic(test_url)
