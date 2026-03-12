import os
import sys
import re
from sqlalchemy import create_engine, text

# Add parent dir to path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def cleanup():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return

    engine = create_engine(database_url)
    bullet_pattern = re.compile(r'^[\s\-_•*\\.]+')

    print("🚀 Starting Campaign Conditions Cleanup...")
    
    with engine.connect() as conn:
        # Fetch campaigns that have conditions
        result = conn.execute(text("SELECT id, conditions FROM campaigns WHERE conditions IS NOT NULL AND conditions != ''"))
        campaigns = result.fetchall()
        
        updated_count = 0
        for campaign_id, conditions in campaigns:
            if not conditions:
                continue
                
            lines = conditions.split('\n')
            new_lines = []
            changed = False
            
            for line in lines:
                trimmed = line.strip()
                if not trimmed:
                    new_lines.append("")
                    continue
                
                # Check if it starts with a bullet
                if bullet_pattern.match(trimmed):
                    cleaned = bullet_pattern.sub('', trimmed).strip()
                    new_lines.append(cleaned)
                    changed = True
                else:
                    new_lines.append(trimmed)
            
            if changed:
                new_conditions = "\n".join(new_lines)
                conn.execute(
                    text("UPDATE campaigns SET conditions = :cond WHERE id = :id"),
                    {"cond": new_conditions, "id": campaign_id}
                )
                updated_count += 1
                if updated_count % 50 == 0:
                    print(f"   ✅ Processed {updated_count} campaigns...")

        conn.commit()
        print(f"\n🎉 Cleanup Finished! Total campaigns updated: {updated_count}")

if __name__ == "__main__":
    cleanup()
