#!/bin/bash

# ============================================================================
# Football Predictor Pro - Project Setup Script
# ============================================================================
# Bu script proje yapısını oluşturur ve konfigürasyon dosyalarını hazırlar
# Kullanım: chmod +x setup.sh && ./setup.sh
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(pwd)"

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║           Football Predictor Pro - Project Setup                  ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================================
# 1. CREATE DIRECTORY STRUCTURE
# ============================================================================

echo -e "${YELLOW}[1/5] Creating directory structure...${NC}"

# Apps - Web (Next.js)
mkdir -p apps/web/app/\(auth\)/login
mkdir -p apps/web/app/\(auth\)/register
mkdir -p apps/web/app/\(dashboard\)/matches
mkdir -p apps/web/app/\(dashboard\)/predictions
mkdir -p apps/web/app/\(dashboard\)/analytics
mkdir -p apps/web/app/\(dashboard\)/news
mkdir -p apps/web/app/\(dashboard\)/teams
mkdir -p apps/web/app/\(dashboard\)/players
mkdir -p apps/web/app/\(dashboard\)/settings
mkdir -p apps/web/app/api/auth
mkdir -p apps/web/app/api/matches
mkdir -p apps/web/app/api/predictions
mkdir -p apps/web/app/api/webhooks
mkdir -p apps/web/components/ui
mkdir -p apps/web/components/dashboard
mkdir -p apps/web/components/matches
mkdir -p apps/web/components/predictions
mkdir -p apps/web/components/charts
mkdir -p apps/web/lib/supabase
mkdir -p apps/web/lib/utils
mkdir -p apps/web/lib/hooks
mkdir -p apps/web/types
mkdir -p apps/web/public

# Apps - Scraper (Python)
mkdir -p apps/scraper/scrapers/odds
mkdir -p apps/scraper/scrapers/news
mkdir -p apps/scraper/processors
mkdir -p apps/scraper/schedulers
mkdir -p apps/scraper/utils
mkdir -p apps/scraper/scripts
mkdir -p apps/scraper/tests

# Packages - AI Engine
mkdir -p packages/ai-engine/models
mkdir -p packages/ai-engine/features
mkdir -p packages/ai-engine/llm/prompts
mkdir -p packages/ai-engine/betting
mkdir -p packages/ai-engine/evaluation
mkdir -p packages/ai-engine/api/routes
mkdir -p packages/ai-engine/api/schemas
mkdir -p packages/ai-engine/tests

# Packages - Database
mkdir -p packages/database/migrations
mkdir -p packages/database/seeds

# Config
mkdir -p config

# Scripts
mkdir -p scripts

# Docs
mkdir -p docs

# Monitoring
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/prometheus

echo -e "${GREEN}✓ Directory structure created${NC}"

# ============================================================================
# 2. CREATE CONFIGURATION FILES
# ============================================================================

echo -e "${YELLOW}[2/5] Creating configuration files...${NC}"

# ----- .env.example -----
cat > .env.example << 'EOF'
# ============================================================================
# Football Predictor Pro - Environment Variables
# ============================================================================
# Copy this file to .env and fill in your values
# ============================================================================

# Database - PostgreSQL
POSTGRES_USER=football_admin
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=football_predictor
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}

# Redis
REDIS_URL=redis://redis:6379

# Supabase (Auth & Realtime)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# AI APIs
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
OPENAI_API_KEY=sk-xxxxx
GOOGLE_API_KEY=xxxxx

# Scraping
PROXY_URL=http://your-proxy:port
SCRAPER_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36

# Notifications
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxx

# Application
NODE_ENV=development
NEXT_PUBLIC_APP_URL=http://localhost:3000
API_URL=http://localhost:8000

# Security
JWT_SECRET=your_jwt_secret_here
ENCRYPTION_KEY=your_encryption_key_here
EOF

# ----- .gitignore -----
cat > .gitignore << 'EOF'
# Dependencies
node_modules/
.pnp
.pnp.js
__pycache__/
*.py[cod]
*$py.class
.Python
venv/
ENV/

# Build outputs
.next/
out/
build/
dist/
*.egg-info/

# Environment
.env
.env.local
.env.*.local

# IDE
.idea/
.vscode/
*.swp
*.swo
.DS_Store

# Logs
logs/
*.log
npm-debug.log*

# Testing
coverage/
.pytest_cache/
htmlcov/

# Database
*.db
*.sqlite

# ML Models
*.pkl
*.joblib
*.h5
models/*.pt
mlruns/

# Misc
.cache/
tmp/
temp/
*.bak
EOF

# ----- docker-compose.yml -----
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # ============================================
  # PostgreSQL Database
  # ============================================
  postgres:
    image: postgres:16-alpine
    container_name: fp_postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./packages/database/migrations:/docker-entrypoint-initdb.d:ro
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - fp_network

  # ============================================
  # Redis Cache & Queue
  # ============================================
  redis:
    image: redis:7-alpine
    container_name: fp_redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - fp_network

  # ============================================
  # Next.js Web Application
  # ============================================
  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    container_name: fp_web
    restart: unless-stopped
    environment:
      NODE_ENV: ${NODE_ENV:-development}
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      NEXT_PUBLIC_SUPABASE_URL: ${SUPABASE_URL}
      NEXT_PUBLIC_SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY}
    ports:
      - "3000:3000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./apps/web:/app
      - /app/node_modules
      - /app/.next
    networks:
      - fp_network

  # ============================================
  # Python Scraper Service
  # ============================================
  scraper:
    build:
      context: ./apps/scraper
      dockerfile: Dockerfile
    container_name: fp_scraper
    restart: unless-stopped
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      PROXY_URL: ${PROXY_URL}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./apps/scraper:/app
    networks:
      - fp_network

  # ============================================
  # Python AI Engine
  # ============================================
  ai-engine:
    build:
      context: ./packages/ai-engine
      dockerfile: Dockerfile
    container_name: fp_ai
    restart: unless-stopped
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      GOOGLE_API_KEY: ${GOOGLE_API_KEY}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./packages/ai-engine:/app
    networks:
      - fp_network

  # ============================================
  # Celery Worker (Background Tasks)
  # ============================================
  celery-worker:
    build:
      context: ./apps/scraper
      dockerfile: Dockerfile
    container_name: fp_celery_worker
    restart: unless-stopped
    command: celery -A schedulers.celery_config worker --loglevel=info
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
    depends_on:
      - redis
      - postgres
    volumes:
      - ./apps/scraper:/app
    networks:
      - fp_network

  # ============================================
  # Celery Beat (Scheduler)
  # ============================================
  celery-beat:
    build:
      context: ./apps/scraper
      dockerfile: Dockerfile
    container_name: fp_celery_beat
    restart: unless-stopped
    command: celery -A schedulers.celery_config beat --loglevel=info
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
    depends_on:
      - redis
      - postgres
    volumes:
      - ./apps/scraper:/app
    networks:
      - fp_network

  # ============================================
  # Adminer (Database Management)
  # ============================================
  adminer:
    image: adminer:latest
    container_name: fp_adminer
    restart: unless-stopped
    ports:
      - "8080:8080"
    depends_on:
      - postgres
    networks:
      - fp_network

  # ============================================
  # Traefik (Reverse Proxy) - Production
  # ============================================
  traefik:
    image: traefik:v3.0
    container_name: fp_traefik
    restart: unless-stopped
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
    ports:
      - "80:80"
      - "443:443"
      - "8081:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik:/etc/traefik:ro
    networks:
      - fp_network

# ============================================
# Networks
# ============================================
networks:
  fp_network:
    driver: bridge

# ============================================
# Volumes
# ============================================
volumes:
  postgres_data:
  redis_data:
EOF

# ----- docker-compose.prod.yml -----
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

# Production overrides
services:
  web:
    build:
      args:
        NODE_ENV: production
    environment:
      NODE_ENV: production
    restart: always

  scraper:
    restart: always

  ai-engine:
    restart: always

  # Add monitoring in production
  prometheus:
    image: prom/prometheus:latest
    container_name: fp_prometheus
    restart: always
    volumes:
      - ./monitoring/prometheus:/etc/prometheus:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "9090:9090"
    networks:
      - fp_network

  grafana:
    image: grafana/grafana:latest
    container_name: fp_grafana
    restart: always
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
    ports:
      - "3001:3000"
    depends_on:
      - prometheus
    networks:
      - fp_network

volumes:
  prometheus_data:
  grafana_data:
EOF

# ----- config/scraper.yaml -----
cat > config/scraper.yaml << 'EOF'
# ============================================================================
# Scraper Configuration
# ============================================================================

scraper:
  # Rate limiting settings
  rate_limit:
    requests_per_minute: 30
    delay_between_requests: 2.0
    max_retries: 3
    retry_delay: 5.0

  # Proxy settings
  proxy:
    enabled: false
    rotation: round_robin  # round_robin, random, sticky
    health_check_interval: 300
    providers: []

  # Browser settings (Playwright)
  browser:
    headless: true
    timeout: 30000
    viewport:
      width: 1920
      height: 1080

  # Data sources configuration
  sources:
    flashscore:
      enabled: true
      base_url: "https://www.flashscore.com"
      schedule: "*/15 * * * *"  # Every 15 minutes
      priority: high
      data_types:
        - live_scores
        - match_stats
        - lineups
        - standings

    sofascore:
      enabled: true
      base_url: "https://www.sofascore.com"
      schedule: "0 */2 * * *"  # Every 2 hours
      priority: high
      data_types:
        - xg_stats
        - player_ratings
        - heat_maps
        - shot_maps

    transfermarkt:
      enabled: true
      base_url: "https://www.transfermarkt.com"
      schedule: "0 6 * * *"  # Daily at 6 AM
      priority: medium
      data_types:
        - market_values
        - transfers
        - injuries
        - suspensions

    oddschecker:
      enabled: true
      base_url: "https://www.oddschecker.com"
      schedule: "*/5 * * * *"  # Every 5 minutes
      priority: high
      data_types:
        - match_odds
        - odds_movements

    # News sources
    news:
      bbc_sport:
        enabled: true
        base_url: "https://www.bbc.com/sport/football"
        schedule: "*/30 * * * *"
      sky_sports:
        enabled: true
        base_url: "https://www.skysports.com/football"
        schedule: "*/30 * * * *"
      guardian:
        enabled: true
        base_url: "https://www.theguardian.com/football"
        schedule: "0 * * * *"

# Leagues to track
leagues:
  premier_league:
    id: "premier-league"
    country: "England"
    flashscore_id: "england/premier-league"
    sofascore_id: 17
    enabled: true

# Data retention
retention:
  raw_data_days: 30
  processed_data_days: 365
  predictions_days: 730
EOF

# ----- config/models.yaml -----
cat > config/models.yaml << 'EOF'
# ============================================================================
# ML Models Configuration
# ============================================================================

models:
  # Poisson Distribution Model
  poisson:
    enabled: true
    weight: 0.25
    parameters:
      home_advantage: 0.1
      time_decay: 0.005  # xi parameter for Dixon-Coles
      max_goals: 10

  # Elo Rating System
  elo:
    enabled: true
    weight: 0.20
    parameters:
      k_factor: 32
      home_advantage: 100
      initial_rating: 1500
      regression_factor: 0.1  # Season start regression

  # Dixon-Coles Model
  dixon_coles:
    enabled: true
    weight: 0.25
    parameters:
      rho: -0.13
      time_decay: 0.005
      optimization_method: "L-BFGS-B"

  # XGBoost Model
  xgboost:
    enabled: true
    weight: 0.30
    parameters:
      n_estimators: 200
      max_depth: 6
      learning_rate: 0.05
      subsample: 0.8
      colsample_bytree: 0.8
      min_child_weight: 3
      objective: "multi:softprob"
      eval_metric: "mlogloss"

  # LightGBM Model (Alternative)
  lightgbm:
    enabled: false
    weight: 0.0
    parameters:
      n_estimators: 200
      max_depth: 6
      learning_rate: 0.05
      num_leaves: 31

  # Neural Network Model
  neural_net:
    enabled: false
    weight: 0.0
    parameters:
      hidden_layers: [128, 64, 32]
      dropout: 0.3
      learning_rate: 0.001
      epochs: 100
      batch_size: 32

# Ensemble Configuration
ensemble:
  method: weighted_average  # weighted_average, stacking, voting
  meta_learner: logistic_regression
  confidence_threshold: 0.55
  min_model_agreement: 0.6

# Feature Engineering
features:
  lookback_matches: 10
  h2h_lookback: 20
  time_decay: true
  
  categories:
    - form_features
    - h2h_features
    - goal_features
    - venue_features
    - xg_features
    - team_strength
    - player_features

# Training Configuration
training:
  test_size: 0.2
  cv_folds: 5
  cv_method: time_series  # time_series, stratified
  random_state: 42
  
  hyperparameter_tuning:
    enabled: true
    method: optuna  # optuna, grid_search, random_search
    n_trials: 100

# Evaluation Metrics
evaluation:
  metrics:
    - accuracy
    - log_loss
    - brier_score
    - rps  # Ranked Probability Score
    - calibration_error
    - roi
    - sharpe_ratio
EOF

# ----- config/notifications.yaml -----
cat > config/notifications.yaml << 'EOF'
# ============================================================================
# Notifications Configuration
# ============================================================================

notifications:
  enabled: true
  
  channels:
    telegram:
      enabled: true
      bot_token: "${TELEGRAM_BOT_TOKEN}"
      chat_id: "${TELEGRAM_CHAT_ID}"
      
    discord:
      enabled: false
      webhook_url: "${DISCORD_WEBHOOK_URL}"
    
    email:
      enabled: false
      smtp_host: "smtp.gmail.com"
      smtp_port: 587
      username: "${EMAIL_USERNAME}"
      password: "${EMAIL_PASSWORD}"
      from_address: "alerts@footballpredictor.com"
      to_addresses: []

  # Alert types
  alerts:
    value_bet:
      enabled: true
      min_edge: 0.05
      min_confidence: 0.6
      channels: [telegram]
      
    high_value_bet:
      enabled: true
      min_edge: 0.10
      min_confidence: 0.7
      channels: [telegram, discord]
      
    match_start:
      enabled: false
      minutes_before: 30
      channels: [telegram]
      
    odds_movement:
      enabled: true
      min_change_percent: 10
      channels: [telegram]
      
    system_error:
      enabled: true
      channels: [telegram]

  # Quiet hours (no notifications)
  quiet_hours:
    enabled: true
    start: "23:00"
    end: "07:00"
    timezone: "Europe/Istanbul"
EOF

echo -e "${GREEN}✓ Configuration files created${NC}"

# ============================================================================
# 3. CREATE DOCKER FILES
# ============================================================================

echo -e "${YELLOW}[3/5] Creating Docker files...${NC}"

# ----- apps/web/Dockerfile -----
cat > apps/web/Dockerfile << 'EOF'
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED 1

RUN npm run build

# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
EOF

# ----- apps/scraper/Dockerfile -----
cat > apps/scraper/Dockerfile << 'EOF'
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies
RUN pip install playwright && playwright install --with-deps chromium

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 scraper && chown -R scraper:scraper /app
USER scraper

CMD ["python", "-m", "schedulers.tasks"]
EOF

# ----- packages/ai-engine/Dockerfile -----
cat > packages/ai-engine/Dockerfile << 'EOF'
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 ai && chown -R ai:ai /app
USER ai

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

echo -e "${GREEN}✓ Docker files created${NC}"

# ============================================================================
# 4. CREATE REQUIREMENTS FILES
# ============================================================================

echo -e "${YELLOW}[4/5] Creating requirements files...${NC}"

# ----- apps/scraper/requirements.txt -----
cat > apps/scraper/requirements.txt << 'EOF'
# Web Scraping
playwright>=1.40.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
httpx>=0.25.0
aiohttp>=3.9.0

# Database
psycopg2-binary>=2.9.0
sqlalchemy>=2.0.0
alembic>=1.13.0

# Task Queue
celery>=5.3.0
redis>=5.0.0

# Data Processing
pandas>=2.1.0
numpy>=1.26.0

# Utilities
python-dotenv>=1.0.0
pyyaml>=6.0.0
tenacity>=8.2.0
ratelimit>=2.2.1

# Logging
structlog>=23.2.0
EOF

# ----- packages/ai-engine/requirements.txt -----
cat > packages/ai-engine/requirements.txt << 'EOF'
# Web Framework
fastapi>=0.108.0
uvicorn>=0.25.0
pydantic>=2.5.0

# Database
psycopg2-binary>=2.9.0
sqlalchemy>=2.0.0

# ML/AI Core
numpy>=1.26.0
pandas>=2.1.0
scipy>=1.11.0
scikit-learn>=1.3.0

# Gradient Boosting
xgboost>=2.0.0
lightgbm>=4.2.0

# Deep Learning (optional)
torch>=2.1.0

# LLM SDKs
anthropic>=0.8.0
openai>=1.6.0
google-generativeai>=0.3.0

# Optimization
optuna>=3.4.0

# Model Management
mlflow>=2.9.0
joblib>=1.3.0

# Statistics
statsmodels>=0.14.0

# Utilities
python-dotenv>=1.0.0
pyyaml>=6.0.0
httpx>=0.25.0
redis>=5.0.0

# Logging
structlog>=23.2.0
EOF

echo -e "${GREEN}✓ Requirements files created${NC}"

# ============================================================================
# 5. CREATE EMPTY SOURCE FILES
# ============================================================================

echo -e "${YELLOW}[5/5] Creating source files...${NC}"

# ----- Next.js Files -----
touch apps/web/app/layout.tsx
touch apps/web/app/globals.css
touch apps/web/app/\(auth\)/login/page.tsx
touch apps/web/app/\(auth\)/register/page.tsx
touch apps/web/app/\(dashboard\)/layout.tsx
touch apps/web/app/\(dashboard\)/page.tsx
touch apps/web/app/\(dashboard\)/matches/page.tsx
touch apps/web/app/\(dashboard\)/predictions/page.tsx
touch apps/web/app/\(dashboard\)/analytics/page.tsx
touch apps/web/app/\(dashboard\)/news/page.tsx
touch apps/web/app/\(dashboard\)/teams/page.tsx
touch apps/web/app/\(dashboard\)/players/page.tsx
touch apps/web/app/\(dashboard\)/settings/page.tsx
touch apps/web/app/api/auth/route.ts
touch apps/web/app/api/matches/route.ts
touch apps/web/app/api/predictions/route.ts
touch apps/web/app/api/webhooks/route.ts
touch apps/web/components/ui/.gitkeep
touch apps/web/components/dashboard/sidebar.tsx
touch apps/web/components/dashboard/header.tsx
touch apps/web/components/matches/match-card.tsx
touch apps/web/components/matches/match-list.tsx
touch apps/web/components/predictions/prediction-card.tsx
touch apps/web/components/charts/probability-chart.tsx
touch apps/web/lib/supabase/client.ts
touch apps/web/lib/supabase/server.ts
touch apps/web/lib/utils/index.ts
touch apps/web/lib/hooks/use-matches.ts
touch apps/web/lib/hooks/use-predictions.ts
touch apps/web/types/index.ts
touch apps/web/types/match.ts
touch apps/web/types/prediction.ts

# ----- Scraper Files -----
touch apps/scraper/scrapers/__init__.py
touch apps/scraper/scrapers/base.py
touch apps/scraper/scrapers/flashscore.py
touch apps/scraper/scrapers/sofascore.py
touch apps/scraper/scrapers/transfermarkt.py
touch apps/scraper/scrapers/odds/__init__.py
touch apps/scraper/scrapers/odds/oddschecker.py
touch apps/scraper/scrapers/odds/betfair.py
touch apps/scraper/scrapers/news/__init__.py
touch apps/scraper/scrapers/news/bbc_sport.py
touch apps/scraper/scrapers/news/sky_sports.py
touch apps/scraper/scrapers/news/guardian.py
touch apps/scraper/processors/__init__.py
touch apps/scraper/processors/match_processor.py
touch apps/scraper/processors/stats_processor.py
touch apps/scraper/processors/news_processor.py
touch apps/scraper/schedulers/__init__.py
touch apps/scraper/schedulers/celery_config.py
touch apps/scraper/schedulers/tasks.py
touch apps/scraper/utils/__init__.py
touch apps/scraper/utils/proxy.py
touch apps/scraper/utils/rate_limiter.py
touch apps/scraper/scripts/__init__.py
touch apps/scraper/scripts/init_db.py
touch apps/scraper/scripts/backfill.py
touch apps/scraper/tests/__init__.py
touch apps/scraper/tests/test_scrapers.py

# ----- AI Engine Files -----
touch packages/ai-engine/__init__.py
touch packages/ai-engine/models/__init__.py
touch packages/ai-engine/models/base.py
touch packages/ai-engine/models/poisson.py
touch packages/ai-engine/models/elo.py
touch packages/ai-engine/models/dixon_coles.py
touch packages/ai-engine/models/xgboost_model.py
touch packages/ai-engine/models/lightgbm_model.py
touch packages/ai-engine/models/neural_net.py
touch packages/ai-engine/models/ensemble.py
touch packages/ai-engine/features/__init__.py
touch packages/ai-engine/features/engineering.py
touch packages/ai-engine/features/team_features.py
touch packages/ai-engine/features/player_features.py
touch packages/ai-engine/features/match_features.py
touch packages/ai-engine/llm/__init__.py
touch packages/ai-engine/llm/base.py
touch packages/ai-engine/llm/claude.py
touch packages/ai-engine/llm/openai_gpt.py
touch packages/ai-engine/llm/gemini.py
touch packages/ai-engine/llm/orchestrator.py
touch packages/ai-engine/llm/prompts/__init__.py
touch packages/ai-engine/llm/prompts/sentiment.py
touch packages/ai-engine/llm/prompts/analysis.py
touch packages/ai-engine/llm/prompts/prediction.py
touch packages/ai-engine/betting/__init__.py
touch packages/ai-engine/betting/kelly.py
touch packages/ai-engine/betting/expected_value.py
touch packages/ai-engine/betting/bankroll.py
touch packages/ai-engine/evaluation/__init__.py
touch packages/ai-engine/evaluation/backtesting.py
touch packages/ai-engine/evaluation/metrics.py
touch packages/ai-engine/evaluation/visualization.py
touch packages/ai-engine/api/__init__.py
touch packages/ai-engine/api/main.py
touch packages/ai-engine/api/routes/__init__.py
touch packages/ai-engine/api/routes/predictions.py
touch packages/ai-engine/api/routes/models.py
touch packages/ai-engine/api/routes/health.py
touch packages/ai-engine/api/schemas/__init__.py
touch packages/ai-engine/api/schemas/prediction.py
touch packages/ai-engine/api/schemas/match.py
touch packages/ai-engine/tests/__init__.py
touch packages/ai-engine/tests/test_models.py
touch packages/ai-engine/tests/test_features.py

# ----- Database Files -----
touch packages/database/schema.sql
touch packages/database/migrations/001_initial.sql
touch packages/database/migrations/002_indexes.sql
touch packages/database/migrations/003_views.sql
touch packages/database/seeds/teams.sql
touch packages/database/seeds/leagues.sql

# ----- Docs -----
touch docs/API.md
touch docs/ARCHITECTURE.md
touch docs/DEPLOYMENT.md

# ----- Scripts -----
touch scripts/deploy.sh
touch scripts/backup.sh

# ----- Monitoring -----
touch monitoring/prometheus/prometheus.yml
touch monitoring/grafana/dashboards/.gitkeep

echo -e "${GREEN}✓ Source files created${NC}"

# ============================================================================
# 6. CREATE PACKAGE.JSON FOR WEB APP
# ============================================================================

cat > apps/web/package.json << 'EOF'
{
  "name": "football-predictor-web",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.0.4",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@supabase/supabase-js": "^2.39.0",
    "@tanstack/react-query": "^5.14.0",
    "zustand": "^4.4.7",
    "socket.io-client": "^4.7.2",
    "recharts": "^2.10.3",
    "date-fns": "^2.30.0",
    "zod": "^3.22.4",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.2.0",
    "class-variance-authority": "^0.7.0",
    "lucide-react": "^0.303.0"
  },
  "devDependencies": {
    "typescript": "^5.3.3",
    "@types/node": "^20.10.0",
    "@types/react": "^18.2.45",
    "@types/react-dom": "^18.2.18",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.32",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.56.0",
    "eslint-config-next": "14.0.4"
  }
}
EOF

# ----- next.config.js -----
cat > apps/web/next.config.js << 'EOF'
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  experimental: {
    serverActions: true,
  },
  images: {
    domains: ['sofascore.com', 'flashscore.com', 'tmssl.akamaized.net'],
  },
}

module.exports = nextConfig
EOF

# ----- tailwind.config.js -----
cat > apps/web/tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
      },
    },
  },
  plugins: [],
}
EOF

# ----- tsconfig.json -----
cat > apps/web/tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
EOF

# ============================================================================
# 7. CREATE DATABASE SCHEMA
# ============================================================================

cat > packages/database/migrations/001_initial.sql << 'EOF'
-- ============================================================================
-- Football Predictor Pro - Database Schema
-- ============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- TEAMS
-- ============================================================================
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(100) UNIQUE,
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(10),
    country VARCHAR(50),
    league VARCHAR(50),
    logo_url TEXT,
    stadium VARCHAR(100),
    founded_year INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- PLAYERS
-- ============================================================================
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(100) UNIQUE,
    name VARCHAR(100) NOT NULL,
    team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    position VARCHAR(30),
    nationality VARCHAR(50),
    birth_date DATE,
    height_cm INTEGER,
    weight_kg INTEGER,
    preferred_foot VARCHAR(10),
    market_value DECIMAL(15, 2),
    photo_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- MATCHES
-- ============================================================================
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(100) UNIQUE,
    home_team_id INTEGER REFERENCES teams(id) NOT NULL,
    away_team_id INTEGER REFERENCES teams(id) NOT NULL,
    league VARCHAR(50) NOT NULL,
    season VARCHAR(10) NOT NULL,
    matchday INTEGER,
    match_date TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, live, finished, postponed
    home_score INTEGER,
    away_score INTEGER,
    home_ht_score INTEGER,
    away_ht_score INTEGER,
    venue VARCHAR(100),
    referee VARCHAR(100),
    attendance INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- MATCH STATISTICS
-- ============================================================================
CREATE TABLE match_stats (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    team_id INTEGER REFERENCES teams(id),
    is_home BOOLEAN NOT NULL,
    possession DECIMAL(5, 2),
    shots INTEGER,
    shots_on_target INTEGER,
    shots_off_target INTEGER,
    blocked_shots INTEGER,
    corners INTEGER,
    fouls INTEGER,
    yellow_cards INTEGER,
    red_cards INTEGER,
    offsides INTEGER,
    passes INTEGER,
    pass_accuracy DECIMAL(5, 2),
    crosses INTEGER,
    tackles INTEGER,
    interceptions INTEGER,
    saves INTEGER,
    xg DECIMAL(5, 2),
    xg_open_play DECIMAL(5, 2),
    xg_set_piece DECIMAL(5, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(match_id, team_id)
);

-- ============================================================================
-- LINEUPS
-- ============================================================================
CREATE TABLE lineups (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    team_id INTEGER REFERENCES teams(id),
    player_id INTEGER REFERENCES players(id),
    is_starter BOOLEAN DEFAULT true,
    position VARCHAR(20),
    shirt_number INTEGER,
    minutes_played INTEGER,
    rating DECIMAL(3, 1),
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(match_id, player_id)
);

-- ============================================================================
-- NEWS
-- ============================================================================
CREATE TABLE news (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(200) UNIQUE,
    source VARCHAR(50) NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    author VARCHAR(100),
    image_url TEXT,
    published_at TIMESTAMPTZ NOT NULL,
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    sentiment_score DECIMAL(4, 3), -- -1 to 1
    sentiment_label VARCHAR(20),
    processed BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- News-Team relationship
CREATE TABLE news_teams (
    news_id INTEGER REFERENCES news(id) ON DELETE CASCADE,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    relevance_score DECIMAL(4, 3),
    is_primary BOOLEAN DEFAULT false,
    PRIMARY KEY (news_id, team_id)
);

-- News-Player relationship
CREATE TABLE news_players (
    news_id INTEGER REFERENCES news(id) ON DELETE CASCADE,
    player_id INTEGER REFERENCES players(id) ON DELETE CASCADE,
    relevance_score DECIMAL(4, 3),
    PRIMARY KEY (news_id, player_id)
);

-- ============================================================================
-- ODDS
-- ============================================================================
CREATE TABLE odds (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    bookmaker VARCHAR(50) NOT NULL,
    market_type VARCHAR(30) NOT NULL, -- 1x2, over_under, asian_handicap, btts
    selection VARCHAR(50) NOT NULL,
    odds_value DECIMAL(8, 3) NOT NULL,
    line DECIMAL(5, 2), -- For handicap/over-under markets
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    is_opening BOOLEAN DEFAULT false
);

-- ============================================================================
-- ELO RATINGS
-- ============================================================================
CREATE TABLE elo_ratings (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    rating DECIMAL(8, 2) NOT NULL,
    rating_date DATE NOT NULL,
    matches_played INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(team_id, rating_date)
);

-- ============================================================================
-- PREDICTIONS
-- ============================================================================
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    model_name VARCHAR(50) NOT NULL,
    model_version VARCHAR(20),
    home_win_prob DECIMAL(6, 5) NOT NULL,
    draw_prob DECIMAL(6, 5) NOT NULL,
    away_win_prob DECIMAL(6, 5) NOT NULL,
    expected_home_goals DECIMAL(5, 2),
    expected_away_goals DECIMAL(5, 2),
    confidence DECIMAL(5, 4),
    features_used JSONB,
    reasoning TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- VALUE BETS
-- ============================================================================
CREATE TABLE value_bets (
    id SERIAL PRIMARY KEY,
    prediction_id INTEGER REFERENCES predictions(id) ON DELETE CASCADE,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    bookmaker VARCHAR(50),
    market_type VARCHAR(30),
    selection VARCHAR(50),
    predicted_prob DECIMAL(6, 5) NOT NULL,
    market_odds DECIMAL(8, 3) NOT NULL,
    implied_prob DECIMAL(6, 5) NOT NULL,
    edge DECIMAL(6, 5) NOT NULL,
    expected_value DECIMAL(8, 5),
    kelly_stake DECIMAL(6, 5),
    confidence VARCHAR(20), -- low, medium, high
    recommended BOOLEAN DEFAULT false,
    result VARCHAR(20), -- pending, won, lost, void
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- MODEL PERFORMANCE
-- ============================================================================
CREATE TABLE model_performance (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(50) NOT NULL,
    evaluation_date DATE NOT NULL,
    matches_evaluated INTEGER,
    accuracy DECIMAL(6, 5),
    log_loss DECIMAL(8, 5),
    brier_score DECIMAL(8, 5),
    rps DECIMAL(8, 5),
    calibration_error DECIMAL(8, 5),
    roi DECIMAL(8, 5),
    total_bets INTEGER,
    winning_bets INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(model_name, evaluation_date)
);

-- ============================================================================
-- AUDIT LOG
-- ============================================================================
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    old_data JSONB,
    new_data JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMPTZ DEFAULT NOW()
);
EOF

# ----- 002_indexes.sql -----
cat > packages/database/migrations/002_indexes.sql << 'EOF'
-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Teams
CREATE INDEX idx_teams_country ON teams(country);
CREATE INDEX idx_teams_league ON teams(league);
CREATE INDEX idx_teams_name_trgm ON teams USING gin (name gin_trgm_ops);

-- Players
CREATE INDEX idx_players_team ON players(team_id);
CREATE INDEX idx_players_name_trgm ON players USING gin (name gin_trgm_ops);

-- Matches
CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_matches_league_season ON matches(league, season);
CREATE INDEX idx_matches_home_team ON matches(home_team_id);
CREATE INDEX idx_matches_away_team ON matches(away_team_id);
CREATE INDEX idx_matches_status ON matches(status);

-- Match Stats
CREATE INDEX idx_match_stats_match ON match_stats(match_id);

-- News
CREATE INDEX idx_news_published ON news(published_at DESC);
CREATE INDEX idx_news_source ON news(source);
CREATE INDEX idx_news_sentiment ON news(sentiment_score);
CREATE INDEX idx_news_title_trgm ON news USING gin (title gin_trgm_ops);

-- Odds
CREATE INDEX idx_odds_match ON odds(match_id);
CREATE INDEX idx_odds_bookmaker ON odds(bookmaker);
CREATE INDEX idx_odds_recorded ON odds(recorded_at);

-- Predictions
CREATE INDEX idx_predictions_match ON predictions(match_id);
CREATE INDEX idx_predictions_model ON predictions(model_name);
CREATE INDEX idx_predictions_created ON predictions(created_at DESC);

-- Value Bets
CREATE INDEX idx_value_bets_match ON value_bets(match_id);
CREATE INDEX idx_value_bets_edge ON value_bets(edge DESC);
CREATE INDEX idx_value_bets_result ON value_bets(result);

-- Elo Ratings
CREATE INDEX idx_elo_team_date ON elo_ratings(team_id, rating_date DESC);
EOF

# ----- 003_views.sql -----
cat > packages/database/migrations/003_views.sql << 'EOF'
-- ============================================================================
-- Views
-- ============================================================================

-- Upcoming matches with team details
CREATE OR REPLACE VIEW v_upcoming_matches AS
SELECT 
    m.id,
    m.match_date,
    m.league,
    m.season,
    m.venue,
    ht.name as home_team,
    ht.short_name as home_short,
    at.name as away_team,
    at.short_name as away_short,
    m.status
FROM matches m
JOIN teams ht ON m.home_team_id = ht.id
JOIN teams at ON m.away_team_id = at.id
WHERE m.status = 'scheduled'
ORDER BY m.match_date;

-- Match results with predictions
CREATE OR REPLACE VIEW v_match_predictions AS
SELECT 
    m.id as match_id,
    m.match_date,
    ht.name as home_team,
    at.name as away_team,
    m.home_score,
    m.away_score,
    p.model_name,
    p.home_win_prob,
    p.draw_prob,
    p.away_win_prob,
    p.confidence,
    CASE 
        WHEN m.home_score > m.away_score THEN 'H'
        WHEN m.home_score < m.away_score THEN 'A'
        ELSE 'D'
    END as actual_result,
    CASE 
        WHEN p.home_win_prob > p.draw_prob AND p.home_win_prob > p.away_win_prob THEN 'H'
        WHEN p.away_win_prob > p.draw_prob AND p.away_win_prob > p.home_win_prob THEN 'A'
        ELSE 'D'
    END as predicted_result
FROM matches m
JOIN teams ht ON m.home_team_id = ht.id
JOIN teams at ON m.away_team_id = at.id
LEFT JOIN predictions p ON m.id = p.match_id
WHERE m.status = 'finished';

-- Team form (last 5 matches)
CREATE OR REPLACE VIEW v_team_form AS
WITH recent_matches AS (
    SELECT 
        t.id as team_id,
        t.name as team_name,
        m.id as match_id,
        m.match_date,
        CASE WHEN m.home_team_id = t.id THEN m.home_score ELSE m.away_score END as goals_for,
        CASE WHEN m.home_team_id = t.id THEN m.away_score ELSE m.home_score END as goals_against,
        ROW_NUMBER() OVER (PARTITION BY t.id ORDER BY m.match_date DESC) as rn
    FROM teams t
    JOIN matches m ON t.id IN (m.home_team_id, m.away_team_id)
    WHERE m.status = 'finished'
)
SELECT 
    team_id,
    team_name,
    COUNT(*) as matches,
    SUM(CASE WHEN goals_for > goals_against THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN goals_for = goals_against THEN 1 ELSE 0 END) as draws,
    SUM(CASE WHEN goals_for < goals_against THEN 1 ELSE 0 END) as losses,
    SUM(goals_for) as goals_for,
    SUM(goals_against) as goals_against,
    SUM(CASE WHEN goals_for > goals_against THEN 3 WHEN goals_for = goals_against THEN 1 ELSE 0 END) as points
FROM recent_matches
WHERE rn <= 5
GROUP BY team_id, team_name;
EOF

echo -e "${GREEN}✓ Database schema created${NC}"

# ============================================================================
# FINAL MESSAGE
# ============================================================================

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    Setup Complete!                                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Copy .env.example to .env and fill in your credentials"
echo "     ${YELLOW}cp .env.example .env${NC}"
echo ""
echo "  2. Start Docker containers"
echo "     ${YELLOW}docker-compose up -d${NC}"
echo ""
echo "  3. Install web dependencies"
echo "     ${YELLOW}cd apps/web && npm install${NC}"
echo ""
echo "  4. Run database migrations"
echo "     ${YELLOW}docker-compose exec postgres psql -U \$POSTGRES_USER -d \$POSTGRES_DB -f /docker-entrypoint-initdb.d/001_initial.sql${NC}"
echo ""
echo -e "${BLUE}Project structure created at: ${PROJECT_ROOT}${NC}"
echo ""
EOF

chmod +x /home/claude/football-predictor/setup.sh

echo -e "${GREEN}✓ Setup script created and made executable${NC}"
