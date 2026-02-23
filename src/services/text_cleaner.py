import re

def clean_campaign_text(raw_text: str) -> str:
    """
    Simple text cleaner to remove boilerplate banking legal terms.
    Works sentence-by-sentence to avoid deleting useful content
    that happens to be on the same line as boilerplate.
    """
    if not raw_text:
        return ""

    # Patterns that identify PURELY boilerplate sentences.
    # IMPORTANT: Only match sentences that are exclusively legal/technical boilerplate.
    # Do NOT add bank names — they appear in participation instructions too.
    junk_patterns = [
        r"operatörlerin kendi tarifeleri",
        r"taksitlendirme süresi bireysel",
        r"bankamızın kampanyayı durdurma hakkı",
        r"kampanya koşullarına uygun olmayan işlemler",
        r"harcama itirazı durumunda",
        r"taksit kısıtı bulunan ürün grupları",
        r"ödüller nakde çevrilemez",
        r"yasal mevzuat gereği",
        r"kullanılmayan puanlar geri alınacaktır",
        r"iptal edilen işlemlerde.*iade edilmez",
    ]

    # Split text into sentences (by period followed by space/newline, or by newline)
    # Then filter out boilerplate sentences individually
    lines = raw_text.split('\n')
    cleaned_lines = []

    for line in lines:
        trimmed = line.strip()
        if not trimmed:
            continue

        # Split line into sentences by ". " or ".\n"
        sentences = re.split(r'(?<=\.)\s+', trimmed)
        clean_sentences = []
        for sentence in sentences:
            s = sentence.strip()
            if not s:
                continue
            is_junk = any(re.search(p, s, re.IGNORECASE) for p in junk_patterns)
            if not is_junk:
                clean_sentences.append(s)

        if clean_sentences:
            cleaned_lines.append(' '.join(clean_sentences))

    return '\n'.join(cleaned_lines)
