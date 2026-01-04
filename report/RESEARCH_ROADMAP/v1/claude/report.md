# Futbol Analitiği ve Bahis Matematiği: Kapsamlı Akademik Araştırma

Futbol tahmin modellemesi, istatistiksel temellerin üzerine inşa edilen sofistike matematiksel çerçevelere dayanır. **Poisson dağılımı temelli modeller**, özellikle Dixon-Coles yaklaşımı, düşük skorlu maçlarda %3-14 oranında düzeltme sağlarken, **Kelly Criterion** bankroll yönetiminde geometrik büyümeyi maksimize eder. Modern yaklaşımlar xG modellerini, Elo rating sistemlerini ve derin öğrenme mimarilerini entegre ederek tahmin doğruluğunu artırır. Bu rapor, Maher (1982)'den günümüzün GNN mimarilerine kadar uzanan teorik temelleri, matematiksel formülasyonları ve pratik uygulamaları kapsamlı şekilde sunar.

---

## 1. Poisson dağılımı futbol skorlarını nasıl modeller?

### 1.1 Özet

Poisson dağılımı, belirli bir zaman aralığında nadir olayların (gol atma) sayısını modellemek için kullanılır. Futbol maçlarında ev sahibi ve deplasman takımlarının gol sayıları tipik olarak **bağımsız Poisson süreçleri** olarak modellenir, ancak bu varsayım düşük skorlu maçlarda ihlal edilir.

### 1.2 Matematiksel Formülasyon

**Temel Poisson Dağılımı:**
$$P(X = k) = \frac{e^{-\lambda}\lambda^k}{k!}$$

Burada $\lambda$ beklenen gol sayısını (ortalama) temsil eder.

**Maher (1982) Orijinal Formülasyonu:**
$$\lambda_{home} = \alpha_i \cdot \beta_j \cdot \gamma$$
$$\lambda_{away} = \alpha_j \cdot \beta_i$$

- $\alpha_i$ = Takım $i$'nin hücum gücü
- $\beta_j$ = Takım $j$'nin savunma zayıflığı
- $\gamma$ = Ev sahibi avantajı faktörü

### 1.3 Zero-Inflated Poisson (ZIP) Modeli

ZIP, fazla sayıda 0-0 sonucunu modellemek için ek bir $\pi$ parametresi ekler:

$$P(Y = y) = \begin{cases} \pi + (1-\pi)e^{-\lambda} & \text{if } y = 0 \\ (1-\pi)\frac{e^{-\lambda}\lambda^y}{y!} & \text{if } y > 0 \end{cases}$$

**Ne zaman kullanılmalı:** Gözlemlenen sıfırlar Poisson tahminlerini önemli ölçüde aştığında (Vuong testi ile doğrulanır).

### 1.4 Bivariate Poisson vs Independent Poisson

**Bivariate Poisson (Karlis & Ntzoufras, 2003):**
$$P(X=x, Y=y) = e^{-(\lambda_1+\lambda_2+\lambda_3)} \frac{\lambda_1^x}{x!}\frac{\lambda_2^y}{y!} \sum_{k=0}^{\min(x,y)} \binom{x}{k}\binom{y}{k}k!\left(\frac{\lambda_3}{\lambda_1\lambda_2}\right)^k$$

- $\lambda_3$ = kovaryans parametresi
- $\text{Cov}(X,Y) = \lambda_3$
- Korelasyon: $\rho = \frac{\lambda_3}{\sqrt{(\lambda_1+\lambda_3)(\lambda_2+\lambda_3)}}$

**Kritik Bulgu:** $\lambda_3 \approx 0.10$ bile beraberlik tahminlerinde **%6.5 artış** sağlar.

### 1.5 Overdispersion ve Negative Binomial

**Poisson:** $\sigma^2 = \mu$
**Negative Binomial:** $\sigma^2 = \mu + \frac{\mu^2}{\theta}$

**Maher (1982)'nin önemli bulgusu:** Takım-spesifik parametreler dahil edildiğinde Poisson yeterli olur; overdispersion genellikle takım heterojenliğini görmezden gelmekten kaynaklanır.

### 1.6 Python Implementasyonu

```python
import numpy as np
from scipy.stats import poisson

def calculate_lambda(attack_strength, defense_weakness, league_avg, home_adv=1.0):
    """λ parametresi hesaplama"""
    return attack_strength * defense_weakness * league_avg * home_adv

def poisson_match_probability(lambda_home, lambda_away, max_goals=10):
    """Maç sonuç olasılıkları"""
    prob_matrix = np.zeros((max_goals, max_goals))
    for i in range(max_goals):
        for j in range(max_goals):
            prob_matrix[i,j] = poisson.pmf(i, lambda_home) * poisson.pmf(j, lambda_away)
    
    home_win = np.sum(np.tril(prob_matrix, -1))
    draw = np.sum(np.diag(prob_matrix))
    away_win = np.sum(np.triu(prob_matrix, 1))
    
    return {'H': home_win, 'D': draw, 'A': away_win}
```

---

## 2. Dixon-Coles modeli düşük skorları nasıl düzeltir?

### 2.1 Özet

Dixon & Coles (1997), bağımsız Poisson'un düşük skorlu maçları (0-0, 1-0, 0-1, 1-1) eksik tahmin etme sorununu **τ (tau) düzeltme faktörü** ile çözer. Model ayrıca **zaman-azalma** (time-decay) mekanizması ekleyerek son maçlara daha fazla ağırlık verir.

### 2.2 τ (Tau) Düzeltme Faktörü Formülleri

$$\tau_{\lambda,\mu}(x,y) = \begin{cases}
1 - \lambda\mu\rho & \text{if } (x,y) = (0,0) \\
1 + \lambda\rho & \text{if } (x,y) = (0,1) \\
1 + \mu\rho & \text{if } (x,y) = (1,0) \\
1 - \rho & \text{if } (x,y) = (1,1) \\
1 & \text{otherwise}
\end{cases}$$

**Değiştirilmiş Ortak Olasılık:**
$$P(X=x, Y=y) = \tau_{\lambda,\mu}(x,y) \cdot \frac{e^{-\lambda}\lambda^x}{x!} \cdot \frac{e^{-\mu}\mu^y}{y!}$$

### 2.3 ρ (Rho) Korelasyon Parametresi

**-0.13 değeri nereden geliyor?**

Dixon ve Coles (1997), İngiliz ligi ve kupa verilerine (1992-1995) **Maximum Likelihood Estimation (MLE)** uygulayarak bu değeri bulmuştur.

**Lig Bazlı ρ Değerleri:**
- Premier League (2011/12 replikasyonu): ρ = **-0.134**
- Genel bulgu: ρ değeri ligler arasında önemli farklılık gösterebilir
- Bazı çalışmalarda **ρ > 0** bile bulunmuştur

**ρ'nun Yorumu:**
- **ρ < 0:** 0-0 ve 1-1 olasılıklarını artırır, 1-0 ve 0-1'i azaltır
- **ρ = 0:** Standart bağımsız Poisson modeline dönüşür

### 2.4 Zaman-Azalma Faktörü (ξ/xi)

$$\phi(t) = e^{-\xi t}$$

**Yarılanma Ömrü:**
$$t_{1/2} = \frac{\ln(2)}{\xi}$$

**Optimal ξ Değerleri:**
| Kaynak | ξ Değeri | Zaman Birimi | Yarılanma Ömrü |
|--------|----------|--------------|----------------|
| Dixon-Coles (1997) | 0.0065 | yarım-hafta | ~1 yıl |
| opisthokonta.net | 0.0018 | gün | ~385 gün |
| dashee87 | 0.00325 | gün | ~213 gün |

### 2.5 Maximum Likelihood Estimation

**Tam Log-Likelihood Fonksiyonu:**
$$\ell(\theta) = \sum_{k=1}^{n} \phi(t_k) \left[ \log\tau_{\lambda_k,\mu_k}(x_k,y_k) + x_k\log\lambda_k - \lambda_k + y_k\log\mu_k - \mu_k \right]$$

**Python Implementasyonu:**

```python
import numpy as np
from scipy.stats import poisson
from scipy.optimize import minimize

def tau_correction(x, y, lambda_home, mu_away, rho):
    """Dixon-Coles tau düzeltme faktörü"""
    if x == 0 and y == 0:
        return 1 - (lambda_home * mu_away * rho)
    elif x == 0 and y == 1:
        return 1 + (lambda_home * rho)
    elif x == 1 and y == 0:
        return 1 + (mu_away * rho)
    elif x == 1 and y == 1:
        return 1 - rho
    else:
        return 1.0

def dc_log_likelihood(params, data, teams, xi=0.0018):
    """Dixon-Coles log-likelihood"""
    n_teams = len(teams)
    attack = dict(zip(teams, params[:n_teams]))
    defense = dict(zip(teams, params[n_teams:2*n_teams]))
    home_adv = params[-2]
    rho = params[-1]
    
    log_lik = 0
    for _, match in data.iterrows():
        home_team, away_team = match['HomeTeam'], match['AwayTeam']
        x, y = int(match['HomeGoals']), int(match['AwayGoals'])
        t = match.get('days_since', 0)
        
        lambda_home = np.exp(attack[home_team] + defense[away_team] + home_adv)
        mu_away = np.exp(attack[away_team] + defense[home_team])
        
        weight = np.exp(-xi * t)
        tau = tau_correction(x, y, lambda_home, mu_away, rho)
        
        if tau > 0:
            log_lik += weight * (np.log(tau) + 
                                 poisson.logpmf(x, lambda_home) + 
                                 poisson.logpmf(y, mu_away))
    return log_lik
```

### 2.6 Key Insights

- τ düzeltmesi **yalnızca** (0,0), (0,1), (1,0), (1,1) skorlarını etkiler
- ρ ≈ -0.13 tipiktir ancak veri ve lige göre değişebilir
- Tek sezon verisi için ξ ≈ 0 optimal; çoklu sezon için ξ > 0 gerekli
- Minimum **10-15 maç/takım** gereklidir stabil parametreler için

---

## 3. Kelly Criterion bahis boyutunu nasıl optimize eder?

### 3.1 Özet

Kelly Criterion, **geometrik büyüme oranını maksimize eden** optimal bahis boyutunu belirler. J.L. Kelly Jr. (1956) tarafından bilgi teorisi bağlamında geliştirilmiş olup, Thorp (2006) ve MacLean et al. (2011) tarafından bahis ve finansa uyarlanmıştır.

### 3.2 Kelly Formülü ve Derivasyonu

$$f^* = \frac{bp - q}{b} = p - \frac{q}{b}$$

- $f^*$ = optimal bahis oranı (bankroll'un yüzdesi)
- $b$ = net odds (kazanç/bahis)
- $p$ = kazanma olasılığı
- $q = 1 - p$ = kaybetme olasılığı

**Alternatif formlar:**
- Even-money için ($b=1$): $f^* = 2p - 1$
- Edge/Odds formu: $f^* = \frac{\text{Edge}}{\text{Odds}}$

**Derivasyon (Geometrik Ortalama Maksimizasyonu):**

$T$ bahisten sonra bankroll:
$$W_T = W_0(1+bf)^N(1-f)^M$$

Beklenen büyüme oranı:
$$g(f) = p\log(1+bf) + q\log(1-f)$$

$\frac{dg}{df} = 0$ denklemini çözerek:
$$\frac{pb}{1+bf} = \frac{q}{1-f} \Rightarrow f^* = \frac{bp - q}{b}$$

### 3.3 Full Kelly vs Fractional Kelly

| Metrik | Full Kelly | Half Kelly (c=0.5) | Quarter Kelly (c=0.25) |
|--------|------------|-------------------|------------------------|
| Büyüme oranı | 1.00 | 0.75 | 0.4375 |
| Varyans oranı | 1.00 | 0.25 | 0.0625 |
| P(yarıya düşme) | 50% | 11.1% | 1.2% |

**Fractional Kelly büyüme formülü:**
$$\frac{g(cf^*)}{g(f^*)} = c(2-c)$$

**Drawdown olasılığı:**
$$P(V(t)/V_0 \leq x) = x^{(2/c - 1)}$$

| Drawdown | Full Kelly | Half Kelly |
|----------|------------|------------|
| %50 | 50% | 12.5% |
| %25 | 25% | 1.56% |

### 3.4 Kelly Varsayımları ve İhlalleri

**Varsayımlar:**
1. Gerçek olasılıklar ($p$) bilinir
2. Bahisler bağımsızdır
3. Bahis limiti yoktur
4. Sonsuz bölünebilirlik
5. Uzun vadeli perspektif

**Futbol bahislerinde ihlaller:**
- Olasılık tahmini belirsizliği → **Quarter/Half Kelly kullan**
- Bahis korelasyonları (aynı maç, aynı takım)
- Bookmaker limitleri
- Vig/komisyon

### 3.5 Multi-bet Kelly (Eşzamanlı Bahisler)

**İki bağımsız bahis için büyüme fonksiyonu:**
$$g(f_1, f_2) = p_1p_2\log(1+b_1f_1+b_2f_2) + p_1q_2\log(1+b_1f_1-f_2) + q_1p_2\log(1-f_1+b_2f_2) + q_1q_2\log(1-f_1-f_2)$$

**Önemli bulgu:** Eşzamanlı Kelly oranları, tekil Kelly'den **daha düşüktür**.

### 3.6 Expected Value Hesaplama

$$EV = (P_{win} \times \text{Profit}) - (P_{lose} \times \text{Stake})$$

**Edge hesaplama:**
$$\text{Edge} = p(b+1) - 1 = pb - q$$

**Kelly ile ilişki:**
$$f^* = \frac{\text{Edge}}{b}$$

### 3.7 Python Implementasyonu

```python
import numpy as np
from scipy.optimize import minimize

def kelly_fraction(p, b):
    """Optimal Kelly oranı"""
    q = 1 - p
    kelly = (b * p - q) / b
    return max(0, kelly)

def fractional_kelly(p, b, fraction=0.5):
    """Fractional Kelly"""
    return fraction * kelly_fraction(p, b)

def expected_value(p, profit_if_win, stake):
    """Beklenen değer"""
    return p * profit_if_win - (1 - p) * stake

def multi_kelly_growth(fractions, probs, odds):
    """Çoklu bahis büyüme oranı"""
    n = len(fractions)
    total_growth = 0.0
    
    for i in range(2**n):
        outcome_prob = 1.0
        bankroll_change = 0.0
        
        for j in range(n):
            if (i >> j) & 1:
                outcome_prob *= probs[j]
                bankroll_change += odds[j] * fractions[j]
            else:
                outcome_prob *= (1 - probs[j])
                bankroll_change -= fractions[j]
        
        if 1 + bankroll_change > 0:
            total_growth += outcome_prob * np.log(1 + bankroll_change)
        else:
            return float('-inf')
    
    return total_growth

def ruin_probability_kelly(x, c=1.0):
    """Kelly drawdown olasılığı"""
    return x ** (2/c - 1)

# Örnek
print(f"p=0.55, b=1.0: f* = {kelly_fraction(0.55, 1.0):.4f}")
print(f"Half Kelly: f = {fractional_kelly(0.55, 1.0, 0.5):.4f}")
print(f"P(50% drawdown, full Kelly) = {ruin_probability_kelly(0.5, 1.0):.2%}")
print(f"P(50% drawdown, half Kelly) = {ruin_probability_kelly(0.5, 0.5):.2%}")
```

---

## 4. xG modelleri şut kalitesini nasıl ölçer?

### 4.1 Özet

Expected Goals (xG), bir şutun gole dönüşme olasılığını tahmin eder. StatsBomb, Opta ve Understat farklı metodolojiler kullanır; **freeze-frame verisi** içeren StatsBomb en yüksek doğruluğu (AUC ~0.878) sağlar.

### 4.2 Provider Karşılaştırması

| Provider | Metodoloji | AUC | Erişim |
|----------|-----------|-----|--------|
| StatsBomb | XGBoost + freeze-frame | ~0.878 | Kısmi ücretsiz |
| Opta (FBref) | Logistic regression + big chance | ~0.85 | Ücretsiz (FBref) |
| Understat | Shot location/angle/type | ~0.83 | Ücretsiz |

**Korelasyon:** Opta×StatsBomb = 0.92-0.93, StatsBomb×Understat = 0.92-0.93

### 4.3 xG Matematiksel Formülasyonu

$$xG = P(\text{goal} | X) = \sigma(\beta_0 + \beta_1 \cdot \text{distance} + \beta_2 \cdot \text{angle} + ...)$$

Lojistik fonksiyon: $\sigma(z) = \frac{1}{1 + e^{-z}}$

### 4.4 Post-Shot xG (PSxG)

PSxG, şut **atıldıktan sonra** hesaplanır ve şutun kaleye gidiş yönünü içerir.

$$PSxG = P(\text{goal} | X_{\text{shot}}, Y_{\text{placement}}, Z_{\text{height}}, GK_{\text{position}})$$

**Kaleci Değerlendirmesi:**
$$GSAx = PSxG_{\text{faced}} - Goals_{\text{conceded}}$$

### 4.5 xGChain ve xGBuildup

$$xGChain_i = \sum_{p \in Possessions_i} xG(\text{shot}_p)$$

$$xGBuildup_i = \sum_{p \in Possessions_i} xG(\text{shot}_p) \cdot \mathbb{1}[\text{player}_i \notin \{\text{shooter, assister}\}]$$

### 4.6 Expected Threat (xT) - Karun Singh Metodolojisi

$$xT_{x,y} = (s_{x,y} \times g_{x,y}) + (m_{x,y} \times \sum_{z,w} T_{(x,y) \rightarrow (z,w)} \cdot xT_{z,w})$$

- $s_{x,y}$ = şut atma olasılığı
- $g_{x,y}$ = şuttan gol olasılığı
- $m_{x,y}$ = topu hareket ettirme olasılığı
- $T$ = geçiş matrisi

**Iterasyon:** 4-5 iterasyon yakınsama için yeterli.

### 4.7 Pitch Control (Fernandez & Bornn, 2018)

$$PC_{\text{team}}(p, t) = \sigma\left(\sum_{i \in \text{team}} I_i(p, t) - \sum_{j \in \text{opponent}} I_j(p, t)\right)$$

Oyuncu etkisi bivariate normal dağılım ile modellenir.

### 4.8 Python Implementasyonu

```python
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier

def calculate_expected_threat(events_df, grid_size=(16, 12), iterations=5):
    """xT grid hesaplama - Karun Singh metodolojisi"""
    L, W = grid_size
    
    # Olasılık matrislerini hesapla
    shot_count = np.zeros((W, L))
    move_count = np.zeros((W, L))
    goal_count = np.zeros((W, L))
    transition_matrix = np.zeros((W, L, W, L))
    
    # ... veri işleme ...
    
    total_actions = shot_count + move_count
    total_actions[total_actions == 0] = 1
    
    shoot_prob = shot_count / total_actions
    move_prob = move_count / total_actions
    goal_prob = np.divide(goal_count, shot_count, where=shot_count > 0)
    
    # Iteratif hesaplama
    xT = np.zeros((W, L))
    
    for _ in range(iterations):
        xT_new = np.zeros((W, L))
        for y in range(W):
            for x in range(L):
                shoot_value = shoot_prob[y, x] * goal_prob[y, x]
                move_value = move_prob[y, x] * np.sum(transition_prob[y, x] * xT)
                xT_new[y, x] = shoot_value + move_value
        xT = xT_new
    
    return xT
```

---

## 5. Feature engineering tahmin gücünü nasıl artırır?

### 5.1 xG vs Actual Goals: Prediktif Güç

Akademik çalışmalar tutarlı şekilde **xG'nin actual goals'dan daha prediktif** olduğunu gösterir (korelasyon r = 0.78). xG, şansı/varyansı filtreler; düşük performans gösteren takımlar xG'lerine regrese eder.

### 5.2 PPDA (Passes Per Defensive Action)

$$PPDA = \frac{\text{Rakip Pasları (Savunma Bölgesinde)}}{\text{Defansif Aksiyonlar}}$$

**Defansif Bölge:** Sahanın pressing yapan takım açısından **hücuma en yakın %60'lık** kısmı.

| PPDA | Yorum |
|------|-------|
| 4-8 | Yüksek pressing (Liverpool, Man City) |
| 9-12 | Orta pressing |
| 13+ | Düşük blok, pasif savunma |

### 5.3 Field Tilt

$$\text{Field Tilt} = \frac{\text{Takım Son 1/3 Aksiyonları}}{\text{Toplam Son 1/3 Aksiyonları}} \times 100$$

Sezon puanları ile korelasyon: R² ~0.78

### 5.4 Progressive Passes (Wyscout Tanımı)

- **Kendi yarısı → Kendi yarısı:** ≥30m
- **Kendi yarısı → Rakip yarısı:** ≥15m
- **Rakip yarısı → Rakip yarısı:** ≥10m

### 5.5 Data Leakage Önleme

**TimeSeriesSplit vs KFold:**

| Aspect | KFold | TimeSeriesSplit |
|--------|-------|-----------------|
| Shuffling | Evet | Hayır |
| Temporal Order | Yoksayılır | Korunur |
| Data Leakage Riski | Yüksek | Önlenir |

```python
from sklearn.model_selection import TimeSeriesSplit

def time_series_cv(X, y, model, n_splits=5):
    """Doğru cross-validation"""
    tscv = TimeSeriesSplit(n_splits=n_splits)
    scores = []
    
    for train_idx, test_idx in tscv.split(X):
        model.fit(X[train_idx], y[train_idx])
        scores.append(model.score(X[test_idx], y[test_idx]))
    
    return np.mean(scores), np.std(scores)
```

---

## 6. Ensemble modeller nasıl optimize edilir?

### 6.1 Model Averaging vs Stacking

**Simple Averaging:** Tüm modellere eşit ağırlık
**Weighted Averaging:** Brier Score minimize eden ağırlıklar
**Stacking:** Meta-model optimal kombinasyonu öğrenir

### 6.2 Brier Score ile Ağırlık Optimizasyonu

$$BS = \frac{1}{N} \sum_{i=1}^{N} \sum_{j=1}^{K} (p_{ij} - y_{ij})^2$$

```python
from scipy.optimize import minimize

def optimize_weights_brier(models, X_val, y_val):
    """Brier score minimize eden ağırlıklar"""
    predictions = [model.predict_proba(X_val) for model in models]
    
    def brier_objective(weights):
        weights = weights / weights.sum()
        combined = sum(w * p for w, p in zip(weights, predictions))
        y_onehot = np.eye(3)[y_val]
        return ((combined - y_onehot) ** 2).mean()
    
    n = len(models)
    result = minimize(brier_objective, np.ones(n)/n, method='SLSQP',
                     constraints={'type': 'eq', 'fun': lambda w: w.sum() - 1},
                     bounds=[(0, 1)] * n)
    
    return result.x / result.x.sum()
```

---

## 7. Model değerlendirme metrikleri ne ifade eder?

### 7.1 Brier Score

$$BS = \frac{1}{N} \sum_{i=1}^{N} (p_i - o_i)^2$$

**Brier Score Decomposition (Murphy, 1973):**
$$BS = \underbrace{REL}_{\text{Reliability}} - \underbrace{RES}_{\text{Resolution}} + \underbrace{UNC}_{\text{Uncertainty}}$$

- **REL (Reliability):** Kalibrasyon hatası, düşük daha iyi
- **RES (Resolution):** Ayrım gücü, yüksek daha iyi
- **UNC (Uncertainty):** $\bar{o}(1-\bar{o})$, veri setine bağlı

**Brier Skill Score:**
$$BSS = 1 - \frac{BS}{BS_{\text{ref}}}$$

### 7.2 Log Loss (Cross-Entropy)

$$\mathcal{L} = -\frac{1}{N}\sum_{i=1}^{N}\left[y_i \log(p_i) + (1-y_i)\log(1-p_i)\right]$$

**Çok sınıflı (1X2):**
$$\mathcal{L} = -\frac{1}{N}\sum_{i=1}^{N}\sum_{c=1}^{C} y_{i,c} \log(p_{i,c})$$

### 7.3 Ranked Probability Score (RPS)

$$RPS = \frac{1}{r-1}\sum_{i=1}^{r-1}\left(\sum_{j=1}^{i}p_j - \sum_{j=1}^{i}o_j\right)^2$$

**Futbol için önemli:** RPS, ordinal mesafeyi dikkate alır (ev galibiyeti beraberliğe daha yakın).

### 7.4 Calibration Curve

```python
from sklearn.calibration import calibration_curve
import matplotlib.pyplot as plt

prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10)

plt.plot([0, 1], [0, 1], 'k--', label='Perfect')
plt.plot(prob_pred, prob_true, 's-', label='Model')
plt.xlabel('Mean Predicted Probability')
plt.ylabel('Fraction of Positives')
plt.legend()
```

### 7.5 İstatistiksel Anlamlılık

**ROI için Confidence Interval:**
$$CI = \hat{p} \pm z_{\alpha/2} \sqrt{\frac{\hat{p}(1-\hat{p})}{n}}$$

**Gerekli örnek boyutu:**
- **%57 win rate + 2,000 bahis:** %95 güvenle anlamlı
- **300 bahis:** Minimum ön değerlendirme
- **2,000-3,000 bahis:** Sinyal gürültüden baskın

---

## 8. CLV neden önemli bir metrik?

### 8.1 Tanım

**Closing Line Value (CLV):** Bahis yapılan odds ile kapanış odds arasındaki fark.

$$CLV\% = \left(\frac{Close_{\text{decimal}}}{Bet_{\text{decimal}}} - 1\right) \times 100$$

### 8.2 CLV Pozitif ama ROI Negatif Olabilir mi?

**Evet, kesinlikle mümkün:**

1. **Kısa vadeli varyans:** 100-500 bahiste pozitif CLV, negatif ROI verebilir
2. **Soft market CLV:** Kapanış çizgisi zaten verimsiz ise CLV anlamsız
3. **Vig hesaba katılmamış:** Fair odds değil vigged odds'a karşı CLV

**Sonuç:** 2,000+ bahis gerekli CLV ve ROI'nin yakınsaması için.

### 8.3 Pinnacle "True Odds" Varsayımı

**Pinnacle neden benchmark?**
- Düşük margin (%2-3)
- Kazananları kabul eder
- Yüksek likidite

**Araştırma kanıtı:** Pinnacle kapanış odds'ları ile gerçek sonuçlar arasında **r² = 0.997** korelasyon (397,935 maç, Trademate Sports).

---

## 9. Elo sistemi takım güçlerini nasıl ölçer?

### 9.1 Temel Elo Formülü

$$R_{\text{new}} = R_{\text{old}} + K \times G \times (S - E)$$

**Beklenen Skor:**
$$E = \frac{1}{1 + 10^{(R_{\text{opp}} - R_{\text{self}})/400}}$$

### 9.2 Margin of Victory (MOV) Faktörü

**World Football Elo:**
$$G = \begin{cases} 1 & \text{margin} = 1 \\ 1.5 & \text{margin} = 2 \\ 1.75 & \text{margin} = 3 \\ 1.75 + \frac{N-3}{8} & \text{margin} \geq 4 \end{cases}$$

**FiveThirtyEight NFL (autocorrelation düzeltmeli):**
$$G = \frac{\ln(\text{MOV} + 1) \times 2.2}{(ELO_W - ELO_L) \times 0.001 + 2.2}$$

### 9.3 Home Advantage

- **Tipik değer:** +100 Elo puanı
- **COVID-19 etkisi:** Seyircisiz maçlarda avantaj %47 azaldı
- **Lig bazlı:** EPL ~68, Bundesliga ~55, La Liga ~85

### 9.4 K-Faktörü ve Sezon Başı Regression

| Maç Türü | K-Faktörü |
|----------|-----------|
| Hazırlık | 20 |
| Lig | 30 |
| Kupa | 40 |
| Dünya Kupası | 60 |

**Sezon Başı Regression:**
$$R_{\text{new season}} = \bar{R} + \alpha \times (R_{\text{end}} - \bar{R})$$

$\alpha = 0.67$ (1/3 regresyon oranı standart)

### 9.5 Glicko-2 Sistemi

Elo'dan üstün çünkü:
- **Rating Deviation (RD):** Belirsizlik ölçümü
- **Volatility:** Performans tutarlılığı
- **Inaktivite handling:** RD pasif dönemde artar

### 9.6 Python Implementasyonu

```python
def expected_score(rating_a, rating_b):
    return 1 / (1 + 10**((rating_b - rating_a) / 400))

def mov_factor_538(mov, winner_elo, loser_elo):
    """FiveThirtyEight MOV faktörü"""
    elo_diff = winner_elo - loser_elo
    return np.log(mov + 1) * 2.2 / (elo_diff * 0.001 + 2.2)

def update_elo(rating, expected, actual, k=30, mov_factor=1.0):
    return rating + k * mov_factor * (actual - expected)

def regress_rating(end_rating, mean=1500, retention=0.67):
    """Sezon başı regresyon"""
    return mean + retention * (end_rating - mean)
```

---

## 10. İleri ML teknikleri futbol analitiğine nasıl uygulanır?

### 10.1 Graph Neural Networks (GNN)

**Mimari:**
- **Node features:** Oyuncu pozisyonu, takım encoding, hız
- **Edge features:** Oyuncular arası mesafe, pas frekansı

**Graph Attention Network (GAT) update:**
$$h_i^{(l+1)} = \sigma\left(\sum_{j \in \mathcal{N}(i)} \alpha_{ij} W h_j^{(l)}\right)$$

### 10.2 SoccerNet-V2 Dataset

- **500 maç**, 764 saat video
- **~300,000 annotation**, 17 aksiyon sınıfı
- State-of-the-art: ~77% Average-mAP

### 10.3 Transformers for Event Data

**Event Embedding:**
$$e_i = \text{ActionEmbed}(\text{type}_i) + \text{PosEmbed}(x_i, y_i) + \text{TimeEmbed}(t_i)$$

**Self-Attention:**
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

### 10.4 Reinforcement Learning for Betting

**MDP Formülasyonu:**
- **State Space:** Bankroll, model confidence, odds, form
- **Action Space:** {no_bet, bet_home, bet_draw, bet_away} + bet_size
- **Reward:** $R_t = \text{stake} \times (\text{odds} - 1)$ if win, $-\text{stake}$ if loss

**Q-Learning vs Policy Gradient:**
| Aspect | Q-Learning | Policy Gradient |
|--------|------------|-----------------|
| Action space | Discrete için uygun | Continuous için uygun |
| Sample efficiency | Yüksek | Düşük |
| Betting use | Hangi bahis | Bahis boyutu |

### 10.5 SPADL/VAEP Framework

$$V_{\text{VAEP}}(a_i) = \Delta P_{\text{score}}(a_i, t) - \Delta P_{\text{concede}}(a_i, t)$$

---

## Akademik Kaynaklar

### Temel Referanslar

1. **Maher, M.J. (1982).** "Modelling association football scores." *Statistica Neerlandica*, 36(3), 109-118.

2. **Dixon, M.J. & Coles, S.G. (1997).** "Modelling Association Football Scores and Inefficiencies in the Football Betting Market." *JRSS Series C*, 46(2), 265-280.

3. **Kelly, J.L. Jr. (1956).** "A New Interpretation of Information Rate." *Bell System Technical Journal*, 35(4), 917-926.

4. **Thorp, E.O. (2006).** "The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market." *Handbook of Asset and Liability Management*, Elsevier.

5. **Karlis, D. & Ntzoufras, I. (2003).** "Analysis of sports data by using bivariate Poisson models." *JRSS Series D*, 52(3), 381-393.

6. **Hvattum, L.M. & Arntzen, H. (2010).** "Using ELO ratings for match result prediction in association football." *International Journal of Forecasting*, 26(3), 460-470.

7. **Fernandez, J. & Bornn, L. (2018).** "Wide Open Spaces: A statistical technique for measuring space creation in professional soccer." *MIT Sloan Sports Analytics Conference*.

8. **Decroos, T. et al. (2019).** "Actions Speak Louder than Goals: Valuing Player Actions in Soccer." *KDD 2019*.

9. **MacLean, L.C., Thorp, E.O., & Ziemba, W.T. (2011).** "The Kelly Capital Growth Investment Criterion: Theory and Practice." *World Scientific*.

10. **Constantinou, A. & Fenton, N. (2012).** "Solving the problem of inadequate scoring rules for assessing probabilistic football forecasting models." *JQAS*.

### Veri Kaynakları

| Kaynak | Veri Tipi | Erişim |
|--------|-----------|--------|
| StatsBomb Open Data | Event data, 360 | GitHub (ücretsiz) |
| Understat | xG, xA, xGChain | API (ücretsiz) |
| FBref | Opta stats | Web (ücretsiz) |
| Football-Data.co.uk | Sonuçlar, odds | Download (ücretsiz) |
| Transfermarkt | Piyasa değerleri | Scraping |

---

## Implementation TODO Listesi

### Kritik Öncelik
- [ ] Dixon-Coles modeli implementasyonu (MLE ile)
- [ ] Kelly Criterion bankroll simulator
- [ ] xG model (logistic regression baseline)

### Yüksek Öncelik
- [ ] Elo rating sistemi (MOV faktörlü)
- [ ] TimeSeriesSplit cross-validation pipeline
- [ ] Brier Score decomposition analizi

### Orta Öncelik
- [ ] xT grid hesaplama (Karun Singh)
- [ ] Ensemble weight optimization
- [ ] CLV tracking sistemi

### Araştırma Önceliği
- [ ] GNN pass network modeli
- [ ] Event sequence Transformer
- [ ] RL betting agent (DQN)

---

## Sonuç

Futbol analitiği, **istatistiksel modelleme**, **makine öğrenmesi** ve **bahis matematiği** disiplinlerinin kesişiminde yer alır. Dixon-Coles modeli, 30 yıla yakın geçmişine rağmen hala güçlü bir baseline sunarken, xG modelleri ve graph neural networks gibi modern yaklaşımlar tahmin doğruluğunu artırmaktadır. **Kelly Criterion**'un fractional versiyonları (0.25-0.5 Kelly), teorik optimallik ile pratik risk yönetimi arasında denge kurar. Başarılı bir futbol tahmin sistemi, bu tüm bileşenleri **proper scoring rules** (Brier, RPS) ile değerlendirilen, **time-series cross-validation** ile doğrulanmış bir ensemble yapısında birleştirmelidir.