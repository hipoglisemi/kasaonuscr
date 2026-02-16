#!/usr/bin/env python3
"""
Test AI Parser Sector Assignment
Checks if AI is correctly assigning sectors
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.ai_parser import parse_api_campaign

# Test cases from real "Diğer" campaigns
test_cases = [
    {
        "title": "Restoran Harcamasına %10 İndirim! 500 TL'ye Varan!",
        "description": "10-28 Şubat 2026 tarihleri arasında World Nakit Dijital, World Nakit, Play Nakit ön ödemeli kartlar ile farklı günlerde yapacağınız her 1.000 TL ve üzeri restoran harcamanıza %10, toplamda 500 TL'ye varan indirim!",
        "content": "Kampanya 10-28 Şubat 2026 tarihleri arasında geçerlidir. Restoran harcamalarında %10 indirim.",
        "expected_sector": "Restoran & Kafe"
    },
    {
        "title": "Opet'te %5 Akaryakıt İndirimi Fırsatı!",
        "description": "20 Ağustos 2025-28 Şubat 2026 tarihleri arasında UTTS'li aracınızla Opet istasyonlarında yapacağınız her akaryakıt alımına %5 indirim!",
        "content": "UTTS'li araçlarda Opet akaryakıt alımlarında %5 indirim.",
        "expected_sector": "Akaryakıt"
    },
    {
        "title": "IKEA'da Worldcard'la 7.500 TL'ye 6 Taksit!",
        "description": "IKEA'da yapacağınız 7.500 TL ve üzeri alışverişlerde 6 taksit imkanı!",
        "content": "IKEA mağazalarında 7.500 TL ve üzeri alışverişlerde 6 taksit.",
        "expected_sector": "Mobilya & Dekorasyon"
    },
    {
        "title": "Arçelik'te Peşin Fiyatına 9 Taksit!",
        "description": "Arçelik mağazalarında peşin fiyatına 9 taksit fırsatı!",
        "content": "Arçelik beyaz eşya ve elektronik ürünlerinde 9 taksit.",
        "expected_sector": "Elektronik"
    }
]

def test_ai_parser():
    print("🧪 AI Parser Sektör Testi\n")
    print("=" * 70)
    
    correct = 0
    total = len(test_cases)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. TEST:")
        print(f"   Başlık: {test['title']}")
        print(f"   Beklenen Sektör: {test['expected_sector']}")
        
        try:
            result = parse_api_campaign(
                title=test['title'],
                short_description=test['description'],
                content_html=test['content'],
                bank_name="Yapı Kredi"
            )
            
            assigned_sector = result.get('sector', 'Diğer')
            print(f"   AI Sonucu: {assigned_sector}")
            
            if assigned_sector == test['expected_sector']:
                print("   ✅ DOĞRU")
                correct += 1
            else:
                print(f"   ❌ YANLIŞ (Beklenen: {test['expected_sector']})")
                
        except Exception as e:
            print(f"   ❌ HATA: {e}")
    
    print("\n" + "=" * 70)
    print(f"\n📊 Sonuç: {correct}/{total} doğru ({correct/total*100:.1f}%)")
    
    if correct < total:
        print("\n⚠️  AI parser sektör atamasında sorun var!")
        print("   Çözüm: AI prompt'unu iyileştirmemiz gerekiyor.")
    else:
        print("\n✅ AI parser doğru çalışıyor!")
        print("   Sorun başka bir yerde olabilir (örn: veritabanında sektör isimleri eşleşmiyor)")

if __name__ == "__main__":
    test_ai_parser()
