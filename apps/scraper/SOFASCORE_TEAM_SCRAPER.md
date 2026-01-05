# SofaScore Team Data Scraper - Kapsamlı Dokümantasyon

## Genel Bakış

Bu scraper, SofaScore'dan **takım detay sayfasındaki TÜM verileri** eksiksiz şekilde çekmek üzere geliştirilmiştir.

Örnek: https://www.sofascore.com/tr/football/team/manchester-city/17

## Özellikler

### 1. Takım Detay Bilgileri (`scrape_team_details`)
Takımın temel bilgilerini çeker:
- İsim, kısa isim, slug
- Ülke bilgisi
- Kuruluş tarihi
- Stadyum (isim, şehir, kapasite)
- Teknik direktör bilgisi
- Takım renkleri

### 2. Kadro/Oyuncular (`scrape_team_squad`)
Takımın tüm oyuncularını çeker:
- Oyuncu ID, isim, pozisyon
- Forma numarası
- Ülke, doğum tarihi
- Boy, tercih edilen ayak
- Temel istatistikler (gol, asist, maç sayısı, rating)

### 3. Maçlar (`scrape_team_matches`)
Geçmiş ve gelecek maçları çeker:
- Son maçlar (last)
- Gelecek maçlar (next)
- Skor, tarih, rakip takım bilgileri
- Maç durumu (bitti, canlı, planlanan)

### 4. Transferler (`scrape_team_transfers`)
Transfer geçmişini çeker:
- Gelen transferler
- Giden transferler
- Oyuncu bilgisi, transfer ücreti
- Transfer tarihi ve tipi

### 5. Takım İstatistikleri (`scrape_team_stats`)
Detaylı sezon istatistiklerini çeker:
- Hücum, savunma, orta saha istatistikleri
- xG (expected goals) ve diğer gelişmiş metrikler
- Maç başına ortalama değerler

### 6. Oyuncu İstatistikleri (`scrape_player_statistics`)
Her oyuncunun detaylı istatistiklerini çeker:
- Gol, asist, şut, pas istatistikleri
- Dribling, top kapma, müdahale
- xG, xA (expected assists)
- Kart, faul bilgileri
- Kaleci için özel istatistikler

### 7. Kupalar/Başarılar (`scrape_team_trophies`)
Takımın kazandığı kupaları çeker:
- Kupa adı, turnuva bilgisi
- Sezon yılı

### 8. Eksiksiz Takım Verisi (`scrape_complete_team_data`)
Yukarıdaki TÜM verileri tek seferde çeker!

## Kullanım Örnekleri

### Basit Kullanım

```python
import asyncio
from scrapers.sofascore import SofascoreScraper

async def main():
    scraper = SofascoreScraper()

    # Manchester City'nin eksiksiz verilerini çek
    data = await scraper.scrape(
        scrape_type="team_complete",
        team_id=17,
        include_player_stats=False  # True yaparsanız her oyuncunun detaylı stats'ını çeker (daha yavaş)
    )

    print(f"Takım: {data['team_details']['name']}")
    print(f"Kadro: {len(data['squad'])} oyuncu")
    print(f"Son maçlar: {len(data['recent_matches'])}")
    print(f"Transferler: {len(data['transfers']['transfers_in'])} gelen, {len(data['transfers']['transfers_out'])} giden")

asyncio.run(main())
```

### Parça Parça Kullanım

```python
# Sadece takım detayları
details = await scraper.scrape(scrape_type="team_details", team_id=17)

# Sadece kadro
squad = await scraper.scrape(scrape_type="team_squad", team_id=17)

# Sadece son 5 maç
matches = await scraper.scrape(scrape_type="team_matches", team_id=17, match_type="last", count=5)

# Sadece transferler
transfers = await scraper.scrape(scrape_type="team_transfers", team_id=17)

# Sadece istatistikler
stats = await scraper.scrape(scrape_type="team_stats", team_id=17)

# Bir oyuncunun istatistikleri
player_stats = await scraper.scrape(scrape_type="player_stats", player_id=123456)
```

## API Endpoint'leri

Scraper aşağıdaki SofaScore API endpoint'lerini kullanır:

1. `/team/{team_id}` - Takım detayları
2. `/team/{team_id}/players` - Kadro listesi
3. `/team/{team_id}/unique-tournament/17/season/current/top-players/overall` - En iyi oyuncular
4. `/team/{team_id}/events/last/{count}` - Son maçlar
5. `/team/{team_id}/events/next/{count}` - Gelecek maçlar
6. `/team/{team_id}/transfers` - Transfer geçmişi
7. `/team/{team_id}/unique-tournament/17/season/current/statistics` - Takım istatistikleri
8. `/team/{team_id}/trophies` - Kupalar
9. `/player/{player_id}/unique-tournament/17/season/current/statistics/overall` - Oyuncu istatistikleri

## Veri Yapısı

### `scrape_complete_team_data` Çıktısı

```json
{
  "team_id": 17,
  "source": "sofascore",
  "scraped_at": "2026-01-05T...",
  "team_details": {
    "team_id": 17,
    "name": "Manchester City",
    "short_name": "Man City",
    "venue": {
      "name": "Etihad Stadium",
      "city": "Manchester",
      "capacity": 55097
    },
    "manager": {
      "name": "Pep Guardiola",
      "country": "Spain"
    },
    ...
  },
  "squad": [
    {
      "player_id": 12345,
      "name": "Erling Haaland",
      "position": "F",
      "jersey_number": 9,
      "statistics": {
        "goals": 20,
        "assists": 5,
        ...
      }
    },
    ...
  ],
  "team_statistics": { ... },
  "recent_matches": [ ... ],
  "upcoming_matches": [ ... ],
  "transfers": {
    "transfers_in": [ ... ],
    "transfers_out": [ ... ]
  },
  "trophies": [ ... ],
  "player_statistics": [ ... ]  // optional
}
```

## Önemli Notlar

### 1. Rate Limiting
SofaScore API'si rate limiting uygular. BaseScraper sınıfında dakikada 20 istek limiti vardır.

### 2. Cloudflare Koruması
SofaScore, Cloudflare koruması kullanır. Doğrudan HTTP istekleri 403 hatası alabilir. Production ortamında Playwright/browser tabanlı çözüm kullanılması önerilir.

### 3. Team ID Bulma
Takım ID'lerini şu şekilde bulabilirsiniz:
- SofaScore web sitesinde takım sayfasının URL'inden (örn: .../team/manchester-city/17)
- Search API'si kullanarak

### 4. Season ID
Varsayılan olarak "current" kullanılır. Önceki sezonlar için spesifik season_id gerekir.

### 5. Premier League ID
Kod şu anda Premier League (ID: 17) için optimize edilmiştir. Diğer ligler için `PREMIER_LEAGUE_ID` değiştirilmelidir.

## Test

Test scriptleri:
- `test_team_scraper.py` - Tam entegrasyon testi (scraper sınıfını kullanır)
- `test_simple.py` - Basit API endpoint testi (doğrudan HTTP istekleri)

```bash
cd /home/user/football-predictor/apps/scraper
python test_simple.py
```

## Geliştirme Notları

### Eklenen Fonksiyonlar
- `scrape_team_details()` ✓
- `scrape_team_squad()` ✓
- `scrape_team_matches()` ✓
- `scrape_team_transfers()` ✓
- `scrape_player_statistics()` ✓
- `scrape_team_trophies()` ✓
- `scrape_complete_team_data()` ✓

### Ana scrape() Metodu Güncellemeleri
Yeni scrape_type değerleri eklendi:
- `team_complete`
- `team_details`
- `team_squad`
- `team_matches`
- `team_transfers`
- `team_stats`
- `player_stats`

## Sınırlamalar

1. **Cloudflare**: Doğrudan API çağrıları Cloudflare tarafından engellenebilir
2. **Rate Limiting**: Çok hızlı istekler banlanmaya yol açabilir (30 saniye bekleme önerilir)
3. **Unofficial API**: Bu, SofaScore'un resmi bir API'si değildir. Kullanım şartlarını ihlal edebilir.
4. **Data Availability**: Bazı veriler (eski sezonlar, küçük takımlar) mevcut olmayabilir

## İleriye Dönük Geliştirmeler

- [ ] Playwright entegrasyonu ile Cloudflare bypass
- [ ] Daha fazla lig desteği
- [ ] Oyuncu karşılaştırma fonksiyonu
- [ ] Head-to-head maç geçmişi
- [ ] Canlı maç olayları (goal, card, substitution tracking)
- [ ] Veritabanına otomatik kayıt

## Kaynaklar

Web araştırması sırasında kullanılan kaynaklar:
- [victorstdev/sofascore-api-stats](https://github.com/victorstdev/sofascore-api-stats)
- [danielsaban/data-scraping-sofascore](https://github.com/danielsaban/data-scraping-sofascore)
- [sofascore-wrapper PyPI](https://pypi.org/project/sofascore-wrapper/)
- [Betfair Forum - SofaScore API](https://forum.betangel.com/viewtopic.php?t=30462)

---

**Son Güncelleme**: 2026-01-05
**Geliştirici**: Claude Code (Anthropic)
