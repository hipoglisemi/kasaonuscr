"""
Data Quality Auto-Fixer

This script scans active campaigns in the database for missing vital information
(such as short/missing description, missing reward text, etc.). If it finds a
defective campaign, it attempts to fetch the HTML from its tracking_url and
passes it back through the Gemini AI parser to repair the missing fields.
"""

import os
import sys
import time
import requests
from bs4 import BeautifulSoup

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import Campaign
from src.database import get_db_session
from src.services.ai_parser import parse_campaign_data

def fetch_html(url: str) -> str:
    """Attempts to fetch the HTML content of a URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Simple cleanup
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        print(f"      ⚠️ Failed to fetch HTML for {url}: {e}")
        return ""

def run_autofix():
    print("🚀 Starting Data Quality Auto-Fixer...")
    
    try:
        with get_db_session() as db:
            print("\n🔍 Scanning for defective campaigns...")
            
            # Find active campaigns with missing/poor descriptions, reward texts, or conditions
            defective_campaigns = db.query(Campaign).filter(
                Campaign.is_active == True
            ).all() # Querying all active to check in Python to handle length comparisons safely across different SQL dialects
            
            to_fix = []
            for c in defective_campaigns:
                is_defective = False
                reasons = []
                
                if not c.description or len(c.description.strip()) < 15:
                    is_defective = True
                    reasons.append("Missing/Short Description")
                if not c.reward_text or c.reward_text.strip() == "":
                    is_defective = True
                    reasons.append("Missing Reward Text")
                if c.reward_value is None:
                    is_defective = True
                    reasons.append("Missing Reward Value")
                if not c.reward_type or c.reward_type.strip() == "":
                    is_defective = True
                    reasons.append("Missing Reward Type")
                if not c.eligible_cards or c.eligible_cards.strip() == "":
                    is_defective = True
                    reasons.append("Missing Eligible Cards")
                if not c.start_date:
                    is_defective = True
                    reasons.append("Missing Start Date")
                if not c.end_date:
                    is_defective = True
                    reasons.append("Missing End Date")
                if not c.conditions or c.conditions.strip() == "":
                    is_defective = True
                    reasons.append("Missing Conditions")
                    
                if is_defective and c.tracking_url:
                    to_fix.append({"campaign": c, "reasons": reasons})
            
            print(f"⚠️ Found {len(to_fix)} defective campaigns requiring repair.")
            
            if not to_fix:
                print("✅ All active campaigns look healthy! Exiting.")
                return
                
            fixed_count = 0
            
            for item in to_fix:
                c = item["campaign"]
                reasons = ", ".join(item["reasons"])
                print(f"\n🛠️ Fixing: [{c.id}] {c.title[:40]}... (Reasons: {reasons})")
                print(f"   🔗 URL: {c.tracking_url}")
                
                # Fetch fresh HTML
                html_text = fetch_html(c.tracking_url)
                if not html_text or len(html_text) < 50:
                    print(f"   ❌ Could not extract meaningful text from URL. Skipping.")
                    continue
                
                # We limit the text size to save tokens
                text_to_parse = html_text[:15000]
                
                print(f"   🤖 Sending {len(text_to_parse)} characters to Gemini AI for re-parsing...")
                ai_data = parse_campaign_data(
                    raw_text=text_to_parse,
                    title=c.title,
                )
                
                if not ai_data:
                    print(f"   ❌ Gemini AI failed to return data. Skipping.")
                    continue
                    
                # Update logic
                updated = False
                
                if not c.description or len(c.description.strip()) < 15:
                    if ai_data.get("description"):
                        print(f"   ✨ Repaired Description!")
                        c.description = ai_data["description"]
                        updated = True
                        
                if not c.reward_text or c.reward_text.strip() == "":
                    if ai_data.get("reward_text"):
                        print(f"   ✨ Repaired Reward Text!")
                        c.reward_text = ai_data["reward_text"]
                        updated = True
                        
                if c.reward_value is None:
                    if ai_data.get("reward_value") is not None:
                        print(f"   ✨ Repaired Reward Value: {ai_data['reward_value']}")
                        c.reward_value = ai_data["reward_value"]
                        updated = True
                        
                if not c.reward_type or c.reward_type.strip() == "":
                    if ai_data.get("reward_type"):
                        print(f"   ✨ Repaired Reward Type: {ai_data['reward_type']}")
                        c.reward_type = ai_data["reward_type"]
                        updated = True
                        
                if not c.eligible_cards or c.eligible_cards.strip() == "":
                    if ai_data.get("cards") and len(ai_data["cards"]) > 0:
                        cards_str = ", ".join(ai_data["cards"])
                        print(f"   ✨ Repaired Eligible Cards: {cards_str}")
                        c.eligible_cards = cards_str
                        updated = True

                if not c.start_date:
                    if ai_data.get("start_date"):
                        print(f"   ✨ Repaired Start Date: {ai_data['start_date']}")
                        from datetime import datetime
                        try:
                            c.start_date = datetime.strptime(ai_data["start_date"], "%Y-%m-%d")
                            updated = True
                        except: pass

                if not c.end_date:
                    if ai_data.get("end_date"):
                        print(f"   ✨ Repaired End Date: {ai_data['end_date']}")
                        from datetime import datetime
                        try:
                            c.end_date = datetime.strptime(ai_data["end_date"], "%Y-%m-%d")
                            updated = True
                        except: pass
                        
                if not c.conditions or c.conditions.strip() == "":
                    if ai_data.get("conditions"):
                        print(f"   ✨ Repaired Conditions!")
                        c.conditions = "\\n".join(f"- {cond}" for cond in ai_data.get("conditions", []))
                        updated = True
                
                if updated:
                    db.commit()
                    fixed_count += 1
                    print(f"   ✅ Campaign successfully repaired and saved!")
                else:
                    print(f"   ⚠️ AI didn't find the missing data. No changes made.")
                
                # Be gentle to the API limits
                time.sleep(2)
                
            print(f"\n🏁 Auto-fixer complete. Successfully repaired {fixed_count}/{len(to_fix)} campaigns.")
            
    except Exception as e:
        print(f"\n📛 CRITICAL ERROR during auto-fix: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_autofix()
