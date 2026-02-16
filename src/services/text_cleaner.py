import re

def clean_campaign_text(raw_text: str) -> str:
    """
    Simple text cleaner to remove boilerplate banking legal terms.
    This helps reduce token usage and provides cleaner input for the AI.
    Ported from kartavantaj-scraper/src/utils/textCleaner.ts
    """
    if not raw_text:
        return ""

    # Regex patterns for more robust boilerplate matching
    junk_patterns = [
        r"yasal mevzuat gereği",
        r"taksitlendirme süresi bireysel",
        r"operatörlerin kendi tarifeleri",
        r"bankamızın kampanyayı durdurma",
        r"iptal edilen işlemlerde",
        r"yasal mevzuat",
        r"kullanılmayan puanlar geri alınacaktır",
        r"kampanya koşullarına uygun olmayan işlemler",
        r"harcama itirazı durumunda",
        r"taksit kısıtı bulunan ürün grupları",
        r"ödüller nakde çevrilemez",
        r"türkiye iş bankası a\.ş\.",
        r"yapı ve kredi bankası a\.ş\.",
        r"akbank t\.a\.ş\.",
        r"garanti bbva",
        r"qnb finansbank",
        r"denizbank a\.ş\."
    ]

    lines = raw_text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        trimmed = line.strip()
        if not trimmed:
            continue
            
        # If the line matches ANY of the junk patterns, filter it out
        is_junk = False
        for pattern in junk_patterns:
            if re.search(pattern, trimmed, re.IGNORECASE):
                is_junk = True
                break
        
        if not is_junk:
            cleaned_lines.append(trimmed)

    return '\n'.join(cleaned_lines)
