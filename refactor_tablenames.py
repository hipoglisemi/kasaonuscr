import glob
import os
import re

files = glob.glob('src/scrapers/*.py') + ['src/models.py']

updated_count = 0
for f_path in files:
    with open(f_path, 'r') as f:
        content = f.read()
    
    new_content = re.sub(
        r"__tablename__\s*=\s*'campaigns'",
        "__tablename__ = 'test_campaigns' if os.environ.get('TEST_MODE') == '1' else 'campaigns'",
        content
    )
    new_content = re.sub(
        r'__tablename__\s*=\s*"campaigns"',
        '__tablename__ = "test_campaigns" if os.environ.get("TEST_MODE") == "1" else "campaigns"',
        new_content
    )
    
    new_content = re.sub(
        r"__tablename__\s*=\s*'campaign_brands'",
        "__tablename__ = 'test_campaign_brands' if os.environ.get('TEST_MODE') == '1' else 'campaign_brands'",
        new_content
    )
    new_content = re.sub(
        r'__tablename__\s*=\s*"campaign_brands"',
        '__tablename__ = "test_campaign_brands" if os.environ.get("TEST_MODE") == "1" else "campaign_brands"',
        new_content
    )
    
    if new_content != content:
        if 'import os' not in new_content:
            new_content = "import os\n" + new_content
        with open(f_path, 'w') as f:
            f.write(new_content)
        print(f"Updated {f_path}")
        updated_count += 1

print(f"Total files updated: {updated_count}")
