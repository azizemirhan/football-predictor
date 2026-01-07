# 🛠 Football Predictor Pro - Kurulum ve Başlangıç Rehberi

Bu rehber, projeyi yerel ortamınızda veya yeni bir sunucuda nasıl kuracağınızı ve çalıştıracağınızı adım adım açıklar.

## 📋 Ön Gereksinimler

Kuruluma başlamadan önce aşağıdaki araçların bilgisayarınızda yüklü olduğundan emin olun:

*   **Docker & Docker Compose**: Servisleri (PostgreSQL, Redis, vb.) çalıştırmak için.
*   **Node.js (v18+)**: Web arayüzü için.
*   **Python (v3.10+)**: AI Engine ve Scraper için.
*   **Git**: Projeyi klonlamak için.

---

## 🚀 Hızlı Kurulum

### 1. Projeyi Klonlayın

```bash
git clone <repository-url>
cd football-predictor
```

### 2. Otomatik Kurulum Script'ini Çalıştırın

Proje kök dizininde bulunan `setup.sh` scripti, gerekli klasör yapısını oluşturur, örnek konfigürasyon dosyalarını hazırlar ve `.env` dosyasını oluşturur.

```bash
chmod +x setup.sh
./setup.sh
```

Bu işlem `Dockerfile`, `docker-compose.yml` ve `.env` dosyalarını oluşturacaktır.

### 3. Çevresel Değişkenleri Ayarlayın

Otomatik kurulum sonrası `.env` dosyası oluşturulacaktır. Bu dosyayı açın ve aşağıdaki önemli değişkenleri güncelleyin:

```env
# Database
POSTGRES_PASSWORD=guclu_bir_sifre

# AI Provider API Keys
ANTHROPIC_API_KEY=sk-ant-...  # Claude (Önerilen)
OPENAI_API_KEY=sk-...         # Opsiyonel
GOOGLE_API_KEY=...            # Opsiyonel

# Uygulama Ayarları
NODE_ENV=development
```

---

## 🐳 Docker ile Başlatma (Önerilen)

Tüm sistemi (Frontend, AI Engine, Scraper, Database, Redis) tek komutla ayağa kaldırmak için:

```bash
docker-compose up -d --build
```

Bu işlem şunları başlatır:
*   **Web App**: `http://localhost:3000`
*   **AI Engine API**: `http://localhost:8000`
*   **PostgreSQL**: Port 5432
*   **Redis**: Port 6379
*   **Scraper & Celery**: Arka planda çalışır
*   **Adminer**: `http://localhost:8080` (Veritabanı yönetimi için)

**Veritabanı Başlangıç Verileri:**
Docker ilk kez çalıştırıldığında `packages/database/init.sh` scripti otomatik olarak çalışır, tabloları oluşturur ve başlangıç verilerini (ligler, takımlar) yükler.

---

## 💻 Geliştirme Modu (Manuel Başlatma)

Servisleri ayrı ayrı geliştirme modunda çalıştırmak isterseniz:

### 1. Altyapıyı Başlatın (DB & Redis)

Önce veritabanı ve Redis'i Docker ile başlatın:

```bash
docker-compose up -d postgres redis
```

### 2. Web Arayüzünü Başlatın (Next.js)

```bash
cd apps/web
npm install
npm run dev
```
Web arayüzüne `http://localhost:3000` adresinden erişebilirsiniz.

### 3. AI Engine'i Başlatın (Python)

```bash
cd packages/ai-engine
python -m venv venv
source venv/bin/activate  # Windows için: venv\Scripts\activate
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```
API dokümantasyonuna `http://localhost:8000/docs` adresinden erişebilirsiniz.

### 4. Scraper Servisini Kurun

```bash
cd apps/scraper
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🔧 Sorun Giderme

### Port Çakışmaları
Eğer `3000` veya `5432` portları doluysa, `.env` dosyasından veya `docker-compose.yml` üzerinden portları değiştirebilirsiniz veya çakışan servisleri durdurabilirsiniz.

### Veritabanı Bağlantı Hatası
`DATABASE_URL` çevresel değişkeninin `.env` dosyasında doğru ayarlandığından emin olun. Docker içinde host adresi `postgres` iken, yerel geliştirmede `localhost` olmalıdır.

### İzin Sorunları (Linux/Mac)
Script çalıştırma izni hatası alırsanız:
```bash
chmod +x setup.sh packages/database/init.sh
```

---

## 📁 Proje Yapısı

*   `apps/web`: Next.js Frontend uygulaması
*   `apps/scraper`: Veri toplama servisi (Python)
*   `packages/ai-engine`: Tahmin modelleri ve LLM entegrasyonu (Python)
*   `packages/database`: SQL şemaları ve seed verileri
*   `config/`: Sistem konfigürasyon dosyaları

