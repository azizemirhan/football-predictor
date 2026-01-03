# ⚽ Football Predictor Pro

> **Premier League Odaklı, AI Destekli Profesyonel Futbol Tahmin Sistemi**

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://docker.com)
[![Python](https://img.shields.io/badge/Python-3.12-green?logo=python)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](https://nextjs.org)
[![License](https://img.shields.io/badge/License-Private-red)](LICENSE)

---

## 📋 İçindekiler

- [Proje Hakkında](#-proje-hakkında)
- [Sistem Mimarisi](#-sistem-mimarisi)
- [Teknoloji Stack](#-teknoloji-stack)
- [Geliştirme Fazları](#-geliştirme-fazları)
- [Kurulum](#-kurulum)
- [Yapılandırma](#-yapılandırma)
- [Kullanım](#-kullanım)
- [API Dokümantasyonu](#-api-dokümantasyonu)
- [Veri Kaynakları](#-veri-kaynakları)
- [AI/ML Modelleri](#-aiml-modelleri)
- [Katkıda Bulunma](#-katkıda-bulunma)

---

## 🎯 Proje Hakkında

Football Predictor Pro, Premier League maçları için yapay zeka destekli tahmin sistemidir. Sistem şu bileşenleri içerir:

- **Çoklu Veri Kaynağı Entegrasyonu**: Flashscore, Sofascore, Transfermarkt, haber siteleri
- **Gelişmiş İstatistiksel Modeller**: Poisson, Elo Rating, Dixon-Coles
- **Makine Öğrenmesi**: XGBoost, LightGBM, Neural Networks
- **LLM Entegrasyonu**: Claude, GPT-4, Gemini ile haber analizi ve sentiment
- **Value Betting Sistemi**: Kelly Criterion, Expected Value hesaplama
- **Gerçek Zamanlı Dashboard**: Next.js + shadcn/ui ile modern arayüz

### Temel Özellikler

| Özellik | Açıklama |
|---------|----------|
| 🔄 Otomatik Veri Toplama | 7/24 scraping ile güncel veriler |
| 📊 Çoklu Model Ensemble | 5+ farklı tahmin modeli |
| 🤖 AI Sentiment Analizi | Haber ve sosyal medya analizi |
| 💰 Value Bet Tespiti | Otomatik value bet alertleri |
| 📱 Modern Dashboard | Responsive, real-time arayüz |
| 📈 Backtesting | Geçmiş performans analizi |

---

## 🏗 Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     Next.js 14 + shadcn/ui + Tailwind                  │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │ │
│  │  │Dashboard │ │ Matches  │ │Predictions│ │Analytics │ │ Settings │    │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                               API GATEWAY LAYER                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         Traefik Reverse Proxy                          │ │
│  │                    (SSL Termination, Load Balancing)                   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             APPLICATION LAYER                                │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │   Next.js API       │  │   Python FastAPI    │  │   Python Celery     │ │
│  │   Routes            │  │   AI Engine         │  │   Task Queue        │ │
│  │                     │  │                     │  │                     │ │
│  │ • Authentication    │  │ • ML Models         │  │ • Scheduled Jobs    │ │
│  │ • WebSocket         │  │ • LLM Integration   │  │ • Async Processing  │ │
│  │ • REST API          │  │ • Predictions       │  │ • Scraping Tasks    │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │   PostgreSQL    │  │     Redis       │  │        Supabase             │ │
│  │   (Primary DB)  │  │   (Cache/Queue) │  │   (Auth/Realtime)           │ │
│  │                 │  │                 │  │                             │ │
│  │ • Matches       │  │ • Session Cache │  │ • User Authentication      │ │
│  │ • Teams         │  │ • Rate Limiting │  │ • Real-time Subscriptions  │ │
│  │ • Players       │  │ • Job Queue     │  │ • Row Level Security       │ │
│  │ • Predictions   │  │ • Pub/Sub       │  │                             │ │
│  │ • Odds          │  │                 │  │                             │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL DATA SOURCES                              │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐    │
│  │Flashscore │ │ Sofascore │ │Transfermkt│ │ BBC Sport │ │ Oddscheckr│    │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘    │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐    │
│  │Sky Sports │ │ Guardian  │ │ FBRef     │ │Understat  │ │ Twitter/X │    │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Veri Akış Diyagramı

```
                                    SCRAPING FLOW
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Scheduler  │────▶│   Scrapers   │────▶│  Processors  │────▶│   Database   │
│   (Celery)   │     │  (Playwright)│     │   (Pandas)   │     │ (PostgreSQL) │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
      │                                                               │
      │ Trigger                                                       │ Store
      ▼                                                               ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              PREDICTION FLOW                                  │
│                                                                              │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐       │
│  │   Data     │───▶│  Feature   │───▶│   Model    │───▶│  Ensemble  │       │
│  │  Fetcher   │    │ Engineering│    │ Inference  │    │  Combiner  │       │
│  └────────────┘    └────────────┘    └────────────┘    └────────────┘       │
│                                                               │              │
│                                                               ▼              │
│                                      ┌────────────────────────────────────┐  │
│                                      │         LLM ANALYSIS               │  │
│                                      │  ┌──────┐ ┌──────┐ ┌──────┐       │  │
│                                      │  │Claude│ │ GPT-4│ │Gemini│       │  │
│                                      │  └──────┘ └──────┘ └──────┘       │  │
│                                      │         News Sentiment             │  │
│                                      │         Injury Analysis            │  │
│                                      │         Form Assessment            │  │
│                                      └────────────────────────────────────┘  │
│                                                               │              │
│                                                               ▼              │
│                                      ┌────────────────────────────────────┐  │
│                                      │       VALUE BET DETECTION          │  │
│                                      │                                    │  │
│                                      │  Predicted Prob vs Market Odds     │  │
│                                      │  Kelly Criterion Calculation       │  │
│                                      │  Risk Assessment                   │  │
│                                      └────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Modül Bağımlılıkları

```
                              MODULE DEPENDENCIES

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│    ┌─────────┐         ┌─────────┐         ┌─────────┐                     │
│    │   Web   │◀────────│   API   │◀────────│   AI    │                     │
│    │  (Next) │         │(FastAPI)│         │ Engine  │                     │
│    └────┬────┘         └────┬────┘         └────┬────┘                     │
│         │                   │                   │                          │
│         │                   │                   │                          │
│         ▼                   ▼                   ▼                          │
│    ┌─────────────────────────────────────────────────┐                     │
│    │                    Database                     │                     │
│    │                  (PostgreSQL)                   │                     │
│    └─────────────────────────────────────────────────┘                     │
│                              ▲                                             │
│                              │                                             │
│    ┌─────────────────────────┴───────────────────────┐                     │
│    │                    Scraper                       │                     │
│    │                   (Python)                       │                     │
│    └─────────────────────────────────────────────────┘                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠 Teknoloji Stack

### Frontend
| Teknoloji | Versiyon | Kullanım Amacı |
|-----------|----------|----------------|
| Next.js | 14.x | React framework, SSR/SSG |
| shadcn/ui | Latest | UI component library |
| TailwindCSS | 3.x | Utility-first CSS |
| Tanstack Query | 5.x | Data fetching & caching |
| Zustand | 4.x | State management |
| Recharts | 2.x | Data visualization |
| Socket.io Client | 4.x | Real-time updates |

### Backend
| Teknoloji | Versiyon | Kullanım Amacı |
|-----------|----------|----------------|
| Python | 3.12 | Ana backend dili |
| FastAPI | 0.109.x | REST API framework |
| Celery | 5.x | Task queue |
| Playwright | 1.x | Browser automation |
| BeautifulSoup4 | 4.x | HTML parsing |
| Pandas | 2.x | Data processing |
| NumPy | 1.x | Numerical computing |
| SciPy | 1.x | Scientific computing |

### AI/ML
| Teknoloji | Versiyon | Kullanım Amacı |
|-----------|----------|----------------|
| Scikit-learn | 1.x | ML utilities |
| XGBoost | 2.x | Gradient boosting |
| LightGBM | 4.x | Gradient boosting |
| PyTorch | 2.x | Deep learning |
| Anthropic SDK | Latest | Claude API |
| OpenAI SDK | Latest | GPT-4 API |
| Google GenAI | Latest | Gemini API |

### Database & Infrastructure
| Teknoloji | Versiyon | Kullanım Amacı |
|-----------|----------|----------------|
| PostgreSQL | 16.x | Primary database |
| Redis | 7.x | Caching, queue |
| Supabase | Latest | Auth, realtime |
| Docker | 24.x | Containerization |
| Traefik | 3.x | Reverse proxy |
| Grafana | Latest | Monitoring |
| Prometheus | Latest | Metrics |

---

## 📅 Geliştirme Fazları

### Faz 1: Altyapı ve Temel Kurulum (Hafta 1-2)

**Hedef**: Docker ortamı, veritabanı şeması, temel Next.js uygulaması

#### Görevler
- [x] Proje yapısı oluşturma
- [ ] Docker Compose konfigürasyonu
- [ ] PostgreSQL şeması ve migrations
- [ ] Supabase entegrasyonu
- [ ] Next.js temel kurulum
- [ ] shadcn/ui component setup
- [ ] Traefik reverse proxy
- [ ] CI/CD pipeline (GitHub Actions)

#### Çıktılar
- Çalışan Docker ortamı
- Boş veritabanı şeması
- Login/Dashboard sayfaları
- Temel API routes

---

### Faz 2: Veri Toplama Sistemi (Hafta 3-4)

**Hedef**: Scraper'lar, scheduler, veri pipeline

#### Görevler
- [ ] Flashscore scraper
- [ ] Sofascore scraper
- [ ] Transfermarkt scraper
- [ ] Haber scraper'ları (BBC, Sky, Guardian)
- [ ] Odds scraper (Oddschecker)
- [ ] Celery task scheduler
- [ ] Rate limiting ve proxy rotation
- [ ] Data validation ve cleaning

#### Çıktılar
- Otomatik veri toplama sistemi
- Dolu veritabanı (geçmiş veriler)
- Günlük güncelleme pipeline

#### Veri Kaynakları Detayı

```
SCRAPER PRIORITY MAP

HIGH PRIORITY (Günlük):
├── Flashscore
│   ├── Canlı skorlar
│   ├── Maç istatistikleri
│   └── Kadrolar
├── Sofascore
│   ├── xG verileri
│   ├── Oyuncu ratings
│   └── Heat maps
└── Oddschecker
    ├── Bahis oranları
    └── Oran hareketleri

MEDIUM PRIORITY (Haftalık):
├── Transfermarkt
│   ├── Oyuncu değerleri
│   ├── Transfer haberleri
│   └── Sakatlık bilgileri
└── FBRef
    ├── Detaylı istatistikler
    └── Advanced metrics

LOW PRIORITY (Anlık):
├── BBC Sport
├── Sky Sports
├── The Guardian
└── Twitter/X
    └── Haber ve sentiment
```

---

### Faz 3: Temel Tahmin Modelleri (Hafta 5-6)

**Hedef**: İstatistiksel modeller, temel ML

#### Görevler
- [ ] Poisson dağılımı modeli
- [ ] Elo Rating sistemi
- [ ] Dixon-Coles modeli
- [ ] XGBoost classifier
- [ ] Feature engineering pipeline
- [ ] Model training scripts
- [ ] Backtesting framework
- [ ] Model versioning (MLflow)

#### Çıktılar
- 4 temel tahmin modeli
- Backtesting sonuçları
- Model karşılaştırma raporu

---

### Faz 4: LLM Entegrasyonu (Hafta 7-8)

**Hedef**: Claude, GPT-4, Gemini entegrasyonu

#### Görevler
- [ ] LLM abstraction layer
- [ ] Claude sentiment analyzer
- [ ] GPT-4 news summarizer
- [ ] Gemini context analyzer
- [ ] Multi-LLM orchestration
- [ ] Prompt engineering
- [ ] Response caching
- [ ] Cost optimization

#### Çıktılar
- LLM analiz sistemi
- Haber sentiment skorları
- Takım/oyuncu analiz raporları

#### LLM Görev Dağılımı

```
LLM TASK DISTRIBUTION

┌─────────────────────────────────────────────────────────────┐
│                      CLAUDE (Anthropic)                      │
│                                                             │
│  Güçlü Yönler:                                              │
│  • Uzun context analizi                                     │
│  • Mantıksal çıkarım                                        │
│  • Detaylı açıklama                                         │
│                                                             │
│  Görevler:                                                  │
│  • Ana tahmin reasoning                                     │
│  • Geçmiş maç pattern analizi                              │
│  • Risk değerlendirmesi                                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       GPT-4 (OpenAI)                         │
│                                                             │
│  Güçlü Yönler:                                              │
│  • Çok dilli işlem                                          │
│  • Hızlı response                                           │
│  • Geniş bilgi tabanı                                       │
│                                                             │
│  Görevler:                                                  │
│  • Haber özetleme                                           │
│  • Sentiment analizi                                        │
│  • Çok dilli içerik işleme                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      GEMINI (Google)                         │
│                                                             │
│  Güçlü Yönler:                                              │
│  • Çok uzun context window                                  │
│  • Multimodal yetenekler                                    │
│  • Güncel bilgi                                             │
│                                                             │
│  Görevler:                                                  │
│  • Sezon analizi                                            │
│  • Tarihsel pattern bulma                                   │
│  • Video/görsel içerik analizi (gelecek)                   │
└─────────────────────────────────────────────────────────────┘
```

---

### Faz 5: Ensemble ve Value Betting (Hafta 9-10)

**Hedef**: Model birleştirme, value bet sistemi

#### Görevler
- [ ] Ensemble model
- [ ] Weighted averaging
- [ ] Stacking classifier
- [ ] Kelly Criterion calculator
- [ ] Expected Value calculator
- [ ] Bankroll management
- [ ] Alert sistemi (Telegram/Discord)
- [ ] Performance tracking

#### Çıktılar
- Final ensemble model
- Value bet detection
- Alert sistemi
- ROI tracking

---

### Faz 6: Dashboard ve UI (Hafta 11-12)

**Hedef**: Tam fonksiyonel dashboard

#### Görevler
- [ ] Dashboard ana sayfa
- [ ] Maç listesi ve detayları
- [ ] Tahmin görüntüleme
- [ ] Odds karşılaştırma
- [ ] Analytics sayfaları
- [ ] Ayarlar ve profil
- [ ] Mobile responsive
- [ ] Dark/Light mode

#### Çıktılar
- Production-ready UI
- Mobile uyumlu tasarım
- Real-time updates

---

### Faz 7: Optimizasyon ve Deployment (Hafta 13-14)

**Hedef**: Production deployment, optimizasyon

#### Görevler
- [ ] Performance optimizasyonu
- [ ] Security hardening
- [ ] SSL sertifikası
- [ ] Backup stratejisi
- [ ] Monitoring setup (Grafana)
- [ ] Log aggregation
- [ ] Documentation
- [ ] Final testing

#### Çıktılar
- Production sistemi
- Monitoring dashboard
- Tam dokümantasyon

---

## 🚀 Kurulum

### Gereksinimler

- Docker 24.0+
- Docker Compose 2.0+
- Node.js 20+ (local development için)
- Python 3.12+ (local development için)
- Git

### Hızlı Başlangıç

```bash
# Repository'yi klonla
git clone https://github.com/yourusername/football-predictor.git
cd football-predictor

# Setup script'i çalıştır
chmod +x setup.sh
./setup.sh

# Environment dosyasını düzenle
cp .env.example .env
nano .env

# Docker container'ları başlat
docker-compose up -d

# Veritabanını initialize et
docker-compose exec scraper python scripts/init_db.py

# Geçmiş verileri çek (opsiyonel)
docker-compose exec scraper python scripts/backfill.py --seasons 2023,2024
```

### Environment Variables

```bash
# Database
POSTGRES_USER=football_admin
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=football_predictor

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# Redis
REDIS_URL=redis://redis:6379

# AI APIs
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Scraping
PROXY_URL=http://proxy:port
SCRAPER_USER_AGENT=Mozilla/5.0...

# Notifications
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
DISCORD_WEBHOOK_URL=...
```

---

## ⚙️ Yapılandırma

### Scraper Ayarları

```yaml
# config/scraper.yaml
scraper:
  rate_limit:
    requests_per_minute: 30
    delay_between_requests: 2
  
  proxy:
    enabled: true
    rotation: round_robin
    providers:
      - name: primary
        url: ${PROXY_URL}
  
  sources:
    flashscore:
      enabled: true
      schedule: "*/15 * * * *"  # Her 15 dakika
    sofascore:
      enabled: true
      schedule: "0 */2 * * *"   # Her 2 saat
    transfermarkt:
      enabled: true
      schedule: "0 6 * * *"     # Her gün 06:00
```

### Model Ayarları

```yaml
# config/models.yaml
models:
  poisson:
    enabled: true
    weight: 0.25
    parameters:
      home_advantage: 0.1
      
  elo:
    enabled: true
    weight: 0.20
    parameters:
      k_factor: 32
      initial_rating: 1500
      
  dixon_coles:
    enabled: true
    weight: 0.25
    parameters:
      rho: -0.13
      
  xgboost:
    enabled: true
    weight: 0.30
    parameters:
      n_estimators: 100
      max_depth: 6
      learning_rate: 0.1

ensemble:
  method: weighted_average  # or: stacking, voting
  confidence_threshold: 0.6
```

---

## 📊 API Dokümantasyonu

### REST Endpoints

```
BASE URL: https://your-domain.com/api/v1

Authentication:
POST   /auth/login
POST   /auth/register
POST   /auth/refresh

Matches:
GET    /matches                    # Tüm maçlar
GET    /matches/:id                # Maç detayı
GET    /matches/upcoming           # Gelecek maçlar
GET    /matches/:id/stats          # Maç istatistikleri
GET    /matches/:id/prediction     # Maç tahmini

Teams:
GET    /teams                      # Tüm takımlar
GET    /teams/:id                  # Takım detayı
GET    /teams/:id/matches          # Takım maçları
GET    /teams/:id/players          # Takım kadrosu
GET    /teams/:id/form             # Takım formu

Players:
GET    /players                    # Tüm oyuncular
GET    /players/:id                # Oyuncu detayı
GET    /players/:id/stats          # Oyuncu istatistikleri

Predictions:
GET    /predictions                # Tüm tahminler
GET    /predictions/today          # Bugünün tahminleri
GET    /predictions/:id            # Tahmin detayı
POST   /predictions/:id/feedback   # Geri bildirim

Odds:
GET    /odds/:match_id             # Maç oranları
GET    /odds/value-bets            # Value bet listesi

Analytics:
GET    /analytics/performance      # Model performansı
GET    /analytics/roi              # ROI takibi
GET    /analytics/history          # Tahmin geçmişi
```

### WebSocket Events

```javascript
// Client connection
socket.connect('wss://your-domain.com/ws')

// Subscribe to events
socket.emit('subscribe', { channels: ['matches', 'predictions'] })

// Incoming events
socket.on('match:update', (data) => { /* Maç güncellemesi */ })
socket.on('match:goal', (data) => { /* Gol bildirimi */ })
socket.on('prediction:new', (data) => { /* Yeni tahmin */ })
socket.on('value_bet:alert', (data) => { /* Value bet alert */ })
socket.on('odds:change', (data) => { /* Oran değişikliği */ })
```

---

## 📈 Veri Kaynakları

### Birincil Kaynaklar

| Kaynak | Veri Türü | Güncelleme Sıklığı |
|--------|-----------|-------------------|
| Flashscore | Canlı skorlar, istatistikler | Real-time |
| Sofascore | xG, player ratings | Maç sonu |
| Oddschecker | Bahis oranları | Her 5 dk |

### İkincil Kaynaklar

| Kaynak | Veri Türü | Güncelleme Sıklığı |
|--------|-----------|-------------------|
| Transfermarkt | Oyuncu değerleri, transferler | Haftalık |
| FBRef | Advanced stats | Günlük |
| Understat | xG detayları | Maç sonu |

### Haber Kaynakları

| Kaynak | Dil | Öncelik |
|--------|-----|---------|
| BBC Sport | EN | Yüksek |
| Sky Sports | EN | Yüksek |
| The Guardian | EN | Orta |
| ESPN | EN | Orta |

---

## 🤖 AI/ML Modelleri

### İstatistiksel Modeller

1. **Poisson Dağılımı**
   - Gol sayısı tahmini
   - Beklenen gol ortalamaları

2. **Elo Rating**
   - Takım güç sıralaması
   - Dinamik rating güncellemesi

3. **Dixon-Coles**
   - Düşük skorlu maç düzeltmesi
   - Bağımlılık parametresi

### Makine Öğrenmesi

1. **XGBoost Classifier**
   - Maç sonucu tahmini
   - Feature importance analizi

2. **LightGBM**
   - Hızlı training
   - Büyük veri setleri

3. **Neural Network**
   - Derin öğrenme
   - Kompleks pattern'ler

### Ensemble Stratejisi

```
ENSEMBLE ARCHITECTURE

Input Features
      │
      ▼
┌─────────────────────────────────────────┐
│           Feature Engineering            │
│  • Rolling averages                      │
│  • Head-to-head stats                    │
│  • Form indicators                       │
│  • Venue statistics                      │
└─────────────────────────────────────────┘
      │
      ├────────────┬────────────┬────────────┐
      ▼            ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ Poisson │  │   Elo   │  │ XGBoost │  │   LLM   │
│  0.25   │  │  0.20   │  │  0.30   │  │  0.25   │
└─────────┘  └─────────┘  └─────────┘  └─────────┘
      │            │            │            │
      └────────────┴────────────┴────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │    Ensemble     │
              │   Predictions   │
              └─────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │   Value Bet     │
              │   Detection     │
              └─────────────────┘
```

---

## 📁 Proje Yapısı

```
football-predictor/
├── apps/
│   ├── web/                          # Next.js Frontend
│   │   ├── app/
│   │   │   ├── (auth)/
│   │   │   │   ├── login/
│   │   │   │   └── register/
│   │   │   ├── (dashboard)/
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── page.tsx
│   │   │   │   ├── matches/
│   │   │   │   ├── predictions/
│   │   │   │   ├── analytics/
│   │   │   │   ├── news/
│   │   │   │   ├── teams/
│   │   │   │   ├── players/
│   │   │   │   └── settings/
│   │   │   ├── api/
│   │   │   │   ├── auth/
│   │   │   │   ├── matches/
│   │   │   │   ├── predictions/
│   │   │   │   └── webhooks/
│   │   │   ├── layout.tsx
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── ui/                   # shadcn/ui components
│   │   │   ├── dashboard/
│   │   │   ├── matches/
│   │   │   ├── predictions/
│   │   │   └── charts/
│   │   ├── lib/
│   │   │   ├── supabase/
│   │   │   ├── utils/
│   │   │   └── hooks/
│   │   ├── types/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── next.config.js
│   │
│   └── scraper/                      # Python Scraper Service
│       ├── scrapers/
│       │   ├── base.py
│       │   ├── flashscore.py
│       │   ├── sofascore.py
│       │   ├── transfermarkt.py
│       │   ├── odds/
│       │   │   ├── oddschecker.py
│       │   │   └── betfair.py
│       │   └── news/
│       │       ├── bbc_sport.py
│       │       ├── sky_sports.py
│       │       └── guardian.py
│       ├── processors/
│       │   ├── match_processor.py
│       │   ├── stats_processor.py
│       │   └── news_processor.py
│       ├── schedulers/
│       │   ├── celery_config.py
│       │   └── tasks.py
│       ├── utils/
│       │   ├── proxy.py
│       │   └── rate_limiter.py
│       ├── scripts/
│       │   ├── init_db.py
│       │   └── backfill.py
│       ├── Dockerfile
│       └── requirements.txt
│
├── packages/
│   ├── ai-engine/                    # Python AI/ML Service
│   │   ├── models/
│   │   │   ├── base.py
│   │   │   ├── poisson.py
│   │   │   ├── elo.py
│   │   │   ├── dixon_coles.py
│   │   │   ├── xgboost_model.py
│   │   │   ├── lightgbm_model.py
│   │   │   ├── neural_net.py
│   │   │   └── ensemble.py
│   │   ├── features/
│   │   │   ├── engineering.py
│   │   │   ├── team_features.py
│   │   │   ├── player_features.py
│   │   │   └── match_features.py
│   │   ├── llm/
│   │   │   ├── base.py
│   │   │   ├── claude.py
│   │   │   ├── openai_gpt.py
│   │   │   ├── gemini.py
│   │   │   ├── orchestrator.py
│   │   │   └── prompts/
│   │   │       ├── sentiment.py
│   │   │       ├── analysis.py
│   │   │       └── prediction.py
│   │   ├── betting/
│   │   │   ├── kelly.py
│   │   │   ├── expected_value.py
│   │   │   └── bankroll.py
│   │   ├── evaluation/
│   │   │   ├── backtesting.py
│   │   │   ├── metrics.py
│   │   │   └── visualization.py
│   │   ├── api/
│   │   │   ├── main.py
│   │   │   ├── routes/
│   │   │   └── schemas/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── database/                     # Shared Database
│       ├── migrations/
│       │   ├── 001_initial.sql
│       │   ├── 002_indexes.sql
│       │   └── 003_views.sql
│       ├── seeds/
│       │   ├── teams.sql
│       │   └── leagues.sql
│       └── schema.sql
│
├── config/
│   ├── scraper.yaml
│   ├── models.yaml
│   └── notifications.yaml
│
├── scripts/
│   ├── setup.sh
│   ├── deploy.sh
│   └── backup.sh
│
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   └── DEPLOYMENT.md
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .gitignore
├── README.md
└── RESEARCH_ROADMAP.md
```

---

## 📞 İletişim ve Destek

- **Issues**: GitHub Issues
- **Email**: your-email@domain.com

---

## 📄 Lisans

Bu proje özel kullanım içindir. Tüm hakları saklıdır.

---

**Son Güncelleme**: 2025-01-03
