# 🔬 Araştırma ve Geliştirme Yol Haritası

> **Profesyonel Futbol Tahmin Sistemleri için Bilimsel Yaklaşım**

---

## 📋 İçindekiler

1. [Temel Kavramlar](#1-temel-kavramlar)
2. [İstatistiksel Modeller](#2-istatistiksel-modeller)
3. [Makine Öğrenmesi](#3-makine-öğrenmesi)
4. [Gelişmiş Metrikler](#4-gelişmiş-metrikler)
5. [LLM Entegrasyonu](#5-llm-entegrasyonu)
6. [Value Betting Matematiği](#6-value-betting-matematiği)
7. [Akademik Kaynaklar](#7-akademik-kaynaklar)
8. [Araçlar ve Kütüphaneler](#8-araçlar-ve-kütüphaneler)
9. [İleri Araştırma Konuları](#9-ileri-araştırma-konuları)

---

## 1. Temel Kavramlar

### 1.1 Olasılık Teorisi

#### Bayes Teoremi
```
P(A|B) = P(B|A) × P(A) / P(B)

Örnek: P(Ev kazanır | Son 5 galibiyet)
```

#### Monte Carlo Simülasyonu
```python
def monte_carlo_match(home_xg, away_xg, n=10000):
    results = {'H': 0, 'D': 0, 'A': 0}
    for _ in range(n):
        h = np.random.poisson(home_xg)
        a = np.random.poisson(away_xg)
        if h > a: results['H'] += 1
        elif h == a: results['D'] += 1
        else: results['A'] += 1
    return {k: v/n for k, v in results.items()}
```

### 1.2 Temel Metrikler

| Kavram | Açıklama | Kullanım |
|--------|----------|----------|
| **Expected Value** | Uzun vadeli ortalama | Value bet tespiti |
| **Variance** | Sonuç dağılımı | Risk değerlendirme |
| **Correlation** | Değişken ilişkisi | Feature selection |
| **Regression to Mean** | Ortalamaya dönüş | Form normalizasyonu |

---

## 2. İstatistiksel Modeller

### 2.1 Poisson Dağılımı

```
P(X = k) = (λ^k × e^(-λ)) / k!

λ = beklenen gol sayısı
k = gerçekleşen gol
```

**Python:**
```python
from scipy.stats import poisson

class PoissonModel:
    def predict(self, home_attack, away_defense, league_avg, home_adv=0.1):
        home_lambda = league_avg * home_attack * away_defense * (1 + home_adv)
        away_lambda = league_avg * away_attack * home_defense
        
        probs = {'H': 0, 'D': 0, 'A': 0}
        for h in range(10):
            for a in range(10):
                p = poisson.pmf(h, home_lambda) * poisson.pmf(a, away_lambda)
                if h > a: probs['H'] += p
                elif h == a: probs['D'] += p
                else: probs['A'] += p
        return probs
```

### 2.2 Dixon-Coles Modeli

Düşük skorlu maçlar için düzeltme:

```
τ(0,0) = 1 - λμρ
τ(0,1) = 1 + λρ
τ(1,0) = 1 + μρ
τ(1,1) = 1 - ρ

ρ ≈ -0.13 (tipik değer)
```

### 2.3 Elo Rating

```
Beklenen Skor: E = 1 / (1 + 10^((R_B - R_A) / 400))
Güncelleme: R_new = R_old + K × (Actual - Expected)

K-faktörü: 20-40 arası (volatilite)
Home advantage: +100 puan
```

---

## 3. Makine Öğrenmesi

### 3.1 Feature Engineering

**Temel Özellikler:**
```python
features = {
    # Form
    'points_last_5': sum(last_5_results),
    'goals_scored_avg': goals.mean(),
    'goals_conceded_avg': conceded.mean(),
    
    # H2H
    'h2h_win_rate': h2h_wins / h2h_total,
    'h2h_goals_avg': h2h_goals.mean(),
    
    # Venue
    'home_win_rate': home_wins / home_matches,
    'away_win_rate': away_wins / away_matches,
    
    # Advanced
    'xg_avg': xg.mean(),
    'xg_against_avg': xg_against.mean(),
    'ppda': passes / defensive_actions
}
```

### 3.2 XGBoost

```python
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit

params = {
    'n_estimators': 200,
    'max_depth': 5,
    'learning_rate': 0.05,
    'objective': 'multi:softprob',
    'num_class': 3
}

# Önemli: Time Series CV kullan!
tscv = TimeSeriesSplit(n_splits=5)
```

### 3.3 Ensemble

```python
class EnsembleModel:
    def __init__(self):
        self.weights = {
            'poisson': 0.25,
            'elo': 0.20,
            'xgboost': 0.30,
            'llm': 0.25
        }
    
    def predict(self, X):
        predictions = []
        for name, model in self.models.items():
            pred = model.predict_proba(X)
            predictions.append(pred * self.weights[name])
        return np.sum(predictions, axis=0)
```

---

## 4. Gelişmiş Metrikler

### 4.1 Expected Goals (xG)

**Faktörler:**
- Şut mesafesi ve açısı
- Vücut pozisyonu
- Pas türü (through ball, cross)
- Hücum türü (open play, set piece)
- Defans baskısı

**Kaynaklar:**
- Opta xG (profesyonel)
- StatsBomb xG (açık kaynak)
- Understat xG (erişilebilir)

### 4.2 Diğer Metrikler

| Metrik | Açıklama |
|--------|----------|
| **xA** | Expected Assists |
| **xGChain** | Gol zinciri katkısı |
| **PPDA** | Pressing yoğunluğu |
| **Field Tilt** | Rakip yarı sahada süre |
| **Progressive Passes** | İleriye taşıyan paslar |

---

## 5. LLM Entegrasyonu

### 5.1 Görev Dağılımı

```
CLAUDE:
├── Ana tahmin reasoning
├── Risk değerlendirmesi
└── Uzun context analizi

GPT-4:
├── Haber sentiment
├── Çok dilli içerik
└── Hızlı özetler

GEMINI:
├── Sezon analizi
├── Tarihsel patternler
└── Uzun geçmiş
```

### 5.2 Prompt Örneği

```python
SENTIMENT_PROMPT = """
Analyze this football news for {team}'s upcoming match:

{article_text}

Return JSON:
{{
    "sentiment": float (-1 to 1),
    "injury_concern": float (0 to 1),
    "morale": float (-1 to 1),
    "key_factors": [strings]
}}
"""
```

---

## 6. Value Betting Matematiği

### 6.1 Expected Value

```
EV = (P_win × Profit) - (P_lose × Stake)

Örnek:
P = 0.45, Odds = 2.50, Stake = 100
EV = (0.45 × 150) - (0.55 × 100) = +12.5 ✓
```

### 6.2 Kelly Criterion

```
f* = (bp - q) / b

b = odds - 1
p = kazanma olasılığı
q = 1 - p

Önerilen: 1/4 Kelly (risk azaltma)
```

### 6.3 Bankroll Management

```python
class BankrollManager:
    def __init__(self, bankroll, risk='moderate'):
        self.params = {
            'conservative': {'max_stake': 0.02, 'kelly': 0.15},
            'moderate': {'max_stake': 0.05, 'kelly': 0.25},
            'aggressive': {'max_stake': 0.10, 'kelly': 0.40}
        }[risk]
    
    def stake(self, prob, odds):
        kelly = (prob * odds - 1) / (odds - 1)
        kelly *= self.params['kelly']
        return min(kelly, self.params['max_stake']) * self.bankroll
```

---

## 7. Akademik Kaynaklar

### 7.1 Temel Makaleler

| Makale | Yıl | Konu |
|--------|-----|------|
| Dixon & Coles | 1997 | Dixon-Coles modeli |
| Dixon & Robinson | 1998 | Dinamik model |
| Hvattum & Arntzen | 2010 | Elo futbolda |
| Bunker & Thabtah | 2019 | ML incelemesi |

### 7.2 Kitaplar

- "The Numbers Game" - Anderson & Sally
- "Soccermatics" - David Sumpter
- "Expected Goals Philosophy" - James Tippett

### 7.3 Veri Kaynakları

- StatsBomb Open Data
- Football-Data.co.uk
- FBRef / Understat

---

## 8. Araçlar ve Kütüphaneler

### 8.1 Python

```bash
# Core
numpy pandas scipy

# ML
scikit-learn xgboost lightgbm torch

# Scraping
playwright beautifulsoup4 httpx

# LLM
anthropic openai google-generativeai

# Viz
matplotlib plotly
```

### 8.2 Profesyonel Araçlar

| Araç | Kullanım | Maliyet |
|------|----------|---------|
| Opta | Pro data | $$$ |
| StatsBomb | xG data | Freemium |
| Wyscout | Video + data | $$ |

---

## 9. İleri Araştırma Konuları

### 9.1 Cutting-Edge

1. **Graph Neural Networks**
   - Oyuncu etkileşim ağları
   - Pas ağı analizi

2. **Transformers**
   - Maç olayları sequence
   - Taktik pattern recognition

3. **Reinforcement Learning**
   - Dinamik bahis stratejisi
   - Oran hareket tahmini

### 9.2 Araştırma Timeline

```
Q1: Temel modeller (Poisson, Elo, XGBoost)
Q2: Gelişmiş features (xG, LLM sentiment)
Q3: Ensemble optimizasyonu
Q4: İleri teknikler (GNN, Transformer)
```

### 9.3 Başarı Metrikleri

| Metrik | Hedef | Minimum |
|--------|-------|---------|
| Accuracy | >55% | 50% |
| Log Loss | <0.95 | 1.0 |
| ROI | >5% | 0% |
| Sharpe | >1.5 | 0.5 |
| Max Drawdown | <20% | 30% |

---

## 📚 Faydalı Linkler

- **StatsBomb**: https://github.com/statsbomb/open-data
- **FBRef**: https://fbref.com
- **Understat**: https://understat.com
- **Football-Data**: https://football-data.co.uk

---

**Son Güncelleme**: 2025-01-03
