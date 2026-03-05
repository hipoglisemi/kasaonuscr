"""
URL Health Checker

Checks all active campaign tracking_url values by following redirects and
detecting broken/incorrect destinations:
- 404 errors
- Redirects to homepage (not a specific campaign page)
- Connection timeouts
- URLs that redirect to a completely different domain

Reports broken URLs and optionally marks campaigns as inactive.
"""

import os
import sys
import re
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_db_session
from src.models import Campaign
from src.services.ai_parser import AIParser

# Known "homepage" paths — if the final URL ends up here, the URL is broken
HOMEPAGE_PATHS = {
    "/",
    "/kampanyalar",
    "/kampanyalar/",
    "/default.aspx",
    "/home",
    "/index",
    "",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/121.0.0.0 Safari/537.36"
}

REQUEST_TIMEOUT = 5   # reduced: 5 s per request
MAX_WORKERS     = 10  # parallel checks

# ── Gemini fallback for broken URLs ─────────────────────────────────────────
VERIFY_PROMPT = """Sen bir web sayfası analiz asistanısın. Aşağıda, {url} adresinden çekilmiş HTML içeriği var.
Amacımız bu URL'deki '{title}' isimli kampanyanın ulaşılamaz, kaldırılmış, "sayfa bulunamadı" (404) veya "kampanya sona erdi" olup olmadığını anlamaktır.

Eğer sayfa anasayfaya yönlenmiş, "sayfa bulunamadı", "aradığınız içerik yok" ya da "kampanya bitmiştir" diyorsa "status": "dead" döndür.
Eğer kampanya detayları (koşullar, tarihler) başarılı şekilde açılmışsa "status": "alive" döndür.

SADECE JSON döndür:
{{"status": "dead" veya "alive", "reason": "kısa açıklama"}}

Sayfa İçeriği:
{html[:5000]}
"""

def _verify_with_gemini(url: str, title: str) -> dict:
    """Uses Playwright + Gemini to verify if the broken URL is actually dead."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=HEADERS["User-Agent"],
                viewport={"width": 1280, "height": 720}
            )
            page = context.new_page()
            try:
                page.goto(url, timeout=10000, wait_until="domcontentloaded")
                # Wait briefly for dynamic redirects
                page.wait_for_timeout(2000)
                html = page.evaluate("() => document.body.innerText")
            except Exception as e:
                # If Playwright fails (e.g., DNS error), assume dead
                html = f"Page load error: {str(e)}"
            finally:
                context.close()
                browser.close()

        parser = AIParser()
        prompt = VERIFY_PROMPT.format(url=url, title=title, html=html)
        raw_ai = parser._call_ai(prompt, timeout_sec=20)

        import json
        match = re.search(r'\{.*?\}', raw_ai, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"status": "unknown", "reason": "AI parça çözülemedi"}

    except Exception as e:
        return {"status": "error", "reason": str(e)}


def _check_url(url: str) -> dict:
    """Follow redirects and classify the URL health."""
    try:
        resp = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        final_url = resp.url
        status = resp.status_code
        parsed_original = urlparse(url)
        parsed_final = urlparse(final_url)

        # 404 or server error
        if status >= 400:
            return {"ok": False, "reason": f"HTTP {status}", "final_url": final_url}

        # Redirected to a completely different domain
        if parsed_final.netloc and parsed_original.netloc:
            orig_domain = parsed_original.netloc.replace("www.", "")
            final_domain = parsed_final.netloc.replace("www.", "")
            if orig_domain != final_domain:
                return {
                    "ok": False,
                    "reason": f"Domain changed: {orig_domain} → {final_domain}",
                    "final_url": final_url,
                }

        # Redirected to homepage
        final_path = parsed_final.path.rstrip("/")
        if final_path in HOMEPAGE_PATHS or final_path == "" :
            return {
                "ok": False,
                "reason": f"Redirected to homepage ({final_url})",
                "final_url": final_url,
            }

        return {"ok": True, "final_url": final_url, "status": status}

    except requests.exceptions.Timeout:
        return {"ok": False, "reason": "Timeout", "final_url": url}
    except requests.exceptions.ConnectionError as e:
        return {"ok": False, "reason": f"Connection error: {e}", "final_url": url}
    except Exception as e:
        return {"ok": False, "reason": str(e), "final_url": url}


def run_url_health_check(deactivate_broken: bool = False, fix_mode: bool = False):
    print("🚀 Starting URL Health Checker...")
    print(f"   ⚙️  Auto-deactivate broken campaigns: {deactivate_broken}")
    print(f"   🤖  Gemini Fix Mode (double check 404s/redirects): {fix_mode}")
    print(f"   ⚙️  Workers: {MAX_WORKERS}, Timeout: {REQUEST_TIMEOUT}s")

    broken = []
    ok_count = 0

    try:
        with get_db_session() as db:
            campaigns = db.query(Campaign).filter(
                Campaign.is_active == True,
                Campaign.tracking_url != None,
            ).all()

            print(f"   📊 Checking {len(campaigns)} active campaigns in parallel...\n")

            url_to_campaign = {c.tracking_url: c for c in campaigns}
            urls = list(url_to_campaign.keys())

            results = {}
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                future_to_url = {executor.submit(_check_url, url): url for url in urls}
                done_count = 0
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        result = future.result()
                    except Exception as e:
                        result = {"ok": False, "reason": str(e), "final_url": url}
                    results[url] = result
                    done_count += 1
                    if done_count % 25 == 0:
                        print(f"   [{done_count}/{len(urls)}] checked so far...")

            # Process results and optionally deactivate
            deactivated_count = 0
            for url, result in results.items():
                c = url_to_campaign[url]
                if result["ok"]:
                    ok_count += 1
                else:
                    reason = result["reason"]
                    is_timeout = "Timeout" in reason

                    broken.append({
                        "id": c.id,
                        "title": c.title,
                        "url": url,
                        "reason": reason,
                        "final_url": result.get("final_url", ""),
                    })
                    print(f"   ❌ [{c.id}] {c.title[:50]}")
                    print(f"      URL    : {url}")
                    print(f"      Reason : {reason}")
                    
                    # Do not ask Gemini if it's just a timeout (likely anti-bot)
                    if deactivate_broken or fix_mode:
                        should_deactivate = deactivate_broken

                        if fix_mode and not is_timeout:
                            print(f"      🤖 Asking Gemini for verification...")
                            ai_check = _verify_with_gemini(url, c.title)
                            print(f"      🤖 Gemini says: {ai_check.get('status')} ({ai_check.get('reason')})")
                            
                            if ai_check.get("status") == "dead":
                                should_deactivate = True
                            else:
                                should_deactivate = False # Override blind deactivation if Gemini says it's alive

                        if should_deactivate:
                            c.is_active = False
                            deactivated_count += 1
                            print(f"      ⛔ Deactivated.")

            if deactivated_count > 0:
                db.commit()
                print(f"\n   ⛔ Committed {deactivated_count} campaign deactivations.")

            print(f"\n{'='*60}")
            print(f"🏁 URL Health Check complete.")
            print(f"   ✅ OK      : {ok_count}")
            print(f"   ❌ Broken  : {len(broken)}")
            print(f"{'='*60}")

            if broken:
                print("\n📋 Broken campaign summary:")
                for b in sorted(broken, key=lambda x: x['id']):
                    print(f"   [{b['id']}] {b['title'][:50]}")
                    print(f"         {b['url']}")
                    print(f"         → {b['reason']}")

    except Exception as e:
        print(f"\n📛 CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--deactivate",
        action="store_true",
        help="BLINDLY set is_active=False for campaigns with broken/redirecting URLs",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Use Gemini to evaluate broken URLs and ONLY deactivate if confirmed dead",
    )
    args = parser.parse_args()
    run_url_health_check(deactivate_broken=args.deactivate, fix_mode=args.fix)
