# 🔬 Derinlemesine Araştırma Kılavuzu

> **Football Predictor Pro - Matematiksel Temeller ve İleri Algoritmalar**

---

## 📋 İçindekiler

1. [Matematiksel Temeller](#1-matematiksel-temeller)
2. [İstatistiksel Model Detayları](#2-i̇statistiksel-model-detayları)
3. [Makine Öğrenmesi Derinlemesine](#3-makine-öğrenmesi-derinlemesine)
4. [LLM Mühendisliği](#4-llm-mühendisliği)
5. [Betting Matematiği](#5-betting-matematiği)
6. [Veri Bilimi Pipeline](#6-veri-bilimi-pipeline)
7. [Performans Optimizasyonu](#7-performans-optimizasyonu)
8. [Araştırma Protokolleri](#8-araştırma-protokolleri)

---

## 1. Matematiksel Temeller

### 1.1 Olasılık Teorisi Derinlemesine

#### Bayes Teoremi Uygulaması

```
Posterior = (Likelihood × Prior) / Evidence

P(Sonuç|Veriler) = P(Veriler|Sonuç) × P(Sonuç) / P(Veriler)
```

**Futbol Uygulaması:**
```python
class BayesianMatchPredictor:
    """
    Bayesian updating ile dinamik tahmin
    Her yeni bilgi ile prior güncellenir
    """
    
    def __init__(self):
        # Prior: Lig ortalamaları
        self.prior = {'H': 0.46, 'D': 0.26, 'A': 0.28}
        
    def update_with_form(self, home_form: List[str], away_form: List[str]):
        """Son form verisiyle prior'u güncelle"""
        
        # Likelihood hesapla
        home_strength = self._calc_form_strength(home_form)
        away_strength = self._calc_form_strength(away_form)
        
        # Oran farkı
        strength_diff = home_strength - away_strength
        
        # Likelihood functions
        likelihood = {
            'H': self._sigmoid(strength_diff + 0.3),  # Home advantage
            'D': self._normal_pdf(strength_diff, 0, 0.5),
            'A': self._sigmoid(-strength_diff)
        }
        
        # Posterior hesapla
        evidence = sum(likelihood[k] * self.prior[k] for k in ['H', 'D', 'A'])
        
        posterior = {}
        for outcome in ['H', 'D', 'A']:
            posterior[outcome] = (likelihood[outcome] * self.prior[outcome]) / evidence
            
        return posterior
    
    def update_with_h2h(self, h2h_record: Dict):
        """Head-to-head verisiyle güncelle"""
        total = sum(h2h_record.values())
        if total < 3:
            return self.prior  # Yetersiz veri
            
        # H2H likelihood
        alpha = 1  # Laplace smoothing
        likelihood = {
            'H': (h2h_record['H'] + alpha) / (total + 3*alpha),
            'D': (h2h_record['D'] + alpha) / (total + 3*alpha),
            'A': (h2h_record['A'] + alpha) / (total + 3*alpha)
        }
        
        # Combine with current posterior
        return self._combine_distributions(self.prior, likelihood, weight=0.3)
```

#### Markov Zinciri Monte Carlo (MCMC)

```python
class MCMCMatchSimulator:
    """
    MCMC ile posterior dağılım örneklemesi
    Uncertainty quantification için kritik
    """
    
    def __init__(self, n_samples=10000, burn_in=1000):
        self.n_samples = n_samples
        self.burn_in = burn_in
        
    def sample_match_parameters(self, home_data: Dict, away_data: Dict):
        """Metropolis-Hastings ile parametre örnekle"""
        
        # Initial values
        current = {
            'home_attack': home_data['goals_avg'],
            'home_defense': home_data['conceded_avg'],
            'away_attack': away_data['goals_avg'],
            'away_defense': away_data['conceded_avg']
        }
        
        samples = []
        
        for i in range(self.n_samples + self.burn_in):
            # Proposal: Random walk
            proposal = {k: v + np.random.normal(0, 0.1) for k, v in current.items()}
            
            # Ensure positive
            proposal = {k: max(0.1, v) for k, v in proposal.items()}
            
            # Calculate acceptance ratio
            log_ratio = (
                self._log_likelihood(proposal, home_data, away_data) -
                self._log_likelihood(current, home_data, away_data)
            )
            
            # Accept/Reject
            if np.log(np.random.random()) < log_ratio:
                current = proposal
                
            if i >= self.burn_in:
                samples.append(current.copy())
                
        return samples
    
    def predict_with_uncertainty(self, samples: List[Dict]) -> Dict:
        """Sample'lardan tahmin ve belirsizlik hesapla"""
        
        probabilities = {'H': [], 'D': [], 'A': []}
        
        for params in samples:
            home_lambda = params['home_attack'] * params['away_defense']
            away_lambda = params['away_attack'] * params['home_defense']
            
            probs = self._poisson_match_probs(home_lambda, away_lambda)
            for outcome in ['H', 'D', 'A']:
                probabilities[outcome].append(probs[outcome])
                
        return {
            'mean': {k: np.mean(v) for k, v in probabilities.items()},
            'std': {k: np.std(v) for k, v in probabilities.items()},
            'ci_95': {k: (np.percentile(v, 2.5), np.percentile(v, 97.5)) 
                      for k, v in probabilities.items()}
        }
```

### 1.2 Bilgi Teorisi

#### Entropi ve Bilgi Kazancı

```python
class InformationMetrics:
    """
    Shannon entropy ve mutual information
    Feature selection ve model evaluation için
    """
    
    @staticmethod
    def entropy(probs: np.ndarray) -> float:
        """Shannon entropy: H(X) = -Σ p(x) log p(x)"""
        probs = probs[probs > 0]  # Avoid log(0)
        return -np.sum(probs * np.log2(probs))
    
    @staticmethod
    def cross_entropy(true_dist: np.ndarray, pred_dist: np.ndarray) -> float:
        """Cross entropy: H(p,q) = -Σ p(x) log q(x)"""
        pred_dist = np.clip(pred_dist, 1e-10, 1)
        return -np.sum(true_dist * np.log(pred_dist))
    
    @staticmethod
    def kl_divergence(p: np.ndarray, q: np.ndarray) -> float:
        """KL Divergence: DKL(P||Q) = Σ p(x) log(p(x)/q(x))"""
        p = np.clip(p, 1e-10, 1)
        q = np.clip(q, 1e-10, 1)
        return np.sum(p * np.log(p / q))
    
    @staticmethod
    def mutual_information(X: np.ndarray, Y: np.ndarray) -> float:
        """MI: I(X;Y) = H(Y) - H(Y|X)"""
        from sklearn.metrics import mutual_info_score
        return mutual_info_score(X, Y)
    
    def feature_importance_by_mi(self, X: pd.DataFrame, y: np.ndarray) -> pd.Series:
        """Mutual information ile feature ranking"""
        mi_scores = {}
        for col in X.columns:
            if X[col].dtype in ['int64', 'float64']:
                # Discretize continuous variables
                discretized = pd.qcut(X[col], q=10, duplicates='drop').codes
            else:
                discretized = X[col].codes
            mi_scores[col] = self.mutual_information(discretized, y)
        return pd.Series(mi_scores).sort_values(ascending=False)
```

---

## 2. İstatistiksel Model Detayları

### 2.1 Dixon-Coles Model - Tam Implementasyon

```python
from scipy.optimize import minimize
from scipy.stats import poisson

class DixonColesModel:
    """
    Dixon-Coles (1997) modeli
    - Düşük skorlu maçlar için korelasyon düzeltmesi
    - Takım bazlı attack/defense parametreleri
    - Ev sahibi avantajı
    """
    
    def __init__(self, rho_init=-0.13):
        self.rho = rho_init
        self.teams = {}
        self.home_advantage = 0.0
        
    def _tau(self, x: int, y: int, lambda_x: float, mu_y: float, rho: float) -> float:
        """
        Dixon-Coles düzeltme faktörü
        Düşük skorlarda (0-0, 0-1, 1-0, 1-1) bağımlılık düzeltmesi
        """
        if x == 0 and y == 0:
            return 1 - lambda_x * mu_y * rho
        elif x == 0 and y == 1:
            return 1 + lambda_x * rho
        elif x == 1 and y == 0:
            return 1 + mu_y * rho
        elif x == 1 and y == 1:
            return 1 - rho
        else:
            return 1.0
    
    def _match_log_likelihood(self, home_goals: int, away_goals: int,
                               home_attack: float, home_defense: float,
                               away_attack: float, away_defense: float,
                               home_adv: float, rho: float) -> float:
        """Tek maç için log-likelihood"""
        
        lambda_home = home_attack * away_defense * np.exp(home_adv)
        mu_away = away_attack * home_defense
        
        # Poisson probabilities
        p_home = poisson.pmf(home_goals, lambda_home)
        p_away = poisson.pmf(away_goals, mu_away)
        
        # Dixon-Coles correction
        tau = self._tau(home_goals, away_goals, lambda_home, mu_away, rho)
        
        return np.log(p_home * p_away * tau + 1e-10)
    
    def fit(self, matches: pd.DataFrame, max_iter=1000):
        """
        Maximum Likelihood Estimation
        matches: DataFrame with columns [home_team, away_team, home_goals, away_goals]
        """
        
        # Get unique teams
        all_teams = set(matches['home_team']) | set(matches['away_team'])
        self.teams = {team: i for i, team in enumerate(all_teams)}
        n_teams = len(self.teams)
        
        # Initial parameters
        # [attack_1, ..., attack_n, defense_1, ..., defense_n, home_adv, rho]
        x0 = np.concatenate([
            np.ones(n_teams),      # attack
            np.ones(n_teams),      # defense  
            [0.2],                 # home advantage
            [-0.1]                 # rho
        ])
        
        def neg_log_likelihood(params):
            attacks = params[:n_teams]
            defenses = params[n_teams:2*n_teams]
            home_adv = params[-2]
            rho = params[-1]
            
            total_ll = 0
            for _, match in matches.iterrows():
                h_idx = self.teams[match['home_team']]
                a_idx = self.teams[match['away_team']]
                
                ll = self._match_log_likelihood(
                    match['home_goals'], match['away_goals'],
                    attacks[h_idx], defenses[h_idx],
                    attacks[a_idx], defenses[a_idx],
                    home_adv, rho
                )
                total_ll += ll
                
            # Constraint: sum of attacks = n_teams (identifiability)
            penalty = 1000 * (np.sum(attacks) - n_teams) ** 2
            
            return -total_ll + penalty
        
        # Optimize
        result = minimize(
            neg_log_likelihood,
            x0,
            method='L-BFGS-B',
            bounds=[(0.2, 3.0)] * n_teams +  # attacks
                   [(0.2, 3.0)] * n_teams +  # defenses
                   [(0, 0.5)] +              # home_adv
                   [(-0.3, 0.0)],            # rho
            options={'maxiter': max_iter}
        )
        
        # Store results
        self.attacks = dict(zip(self.teams.keys(), result.x[:n_teams]))
        self.defenses = dict(zip(self.teams.keys(), result.x[n_teams:2*n_teams]))
        self.home_advantage = result.x[-2]
        self.rho = result.x[-1]
        
        return self
    
    def predict_proba(self, home_team: str, away_team: str, max_goals: int = 10) -> Dict:
        """Maç sonucu olasılıklarını hesapla"""
        
        lambda_home = (self.attacks[home_team] * 
                       self.defenses[away_team] * 
                       np.exp(self.home_advantage))
        mu_away = self.attacks[away_team] * self.defenses[home_team]
        
        probs = {'H': 0.0, 'D': 0.0, 'A': 0.0}
        score_matrix = np.zeros((max_goals, max_goals))
        
        for i in range(max_goals):
            for j in range(max_goals):
                p = (poisson.pmf(i, lambda_home) * 
                     poisson.pmf(j, mu_away) * 
                     self._tau(i, j, lambda_home, mu_away, self.rho))
                
                score_matrix[i, j] = p
                
                if i > j:
                    probs['H'] += p
                elif i == j:
                    probs['D'] += p
                else:
                    probs['A'] += p
        
        return {
            'probabilities': probs,
            'score_matrix': score_matrix,
            'expected_home_goals': lambda_home,
            'expected_away_goals': mu_away
        }
```

### 2.2 Dinamik Elo Sistemi

```python
class DynamicEloSystem:
    """
    Gelişmiş Elo sistemi:
    - Dinamik K-faktör (maç önemine göre)
    - Gol farkı ayarlaması
    - Ev sahibi avantajı düzeltmesi
    - Sezon başı regresyon
    """
    
    def __init__(self, 
                 initial_rating: float = 1500,
                 home_advantage: float = 100,
                 k_base: float = 20):
        self.ratings = {}
        self.initial_rating = initial_rating
        self.home_advantage = home_advantage
        self.k_base = k_base
        self.history = []
        
    def get_rating(self, team: str) -> float:
        return self.ratings.get(team, self.initial_rating)
    
    def _expected_score(self, rating_a: float, rating_b: float) -> float:
        """Beklenen skor (0-1 arası)"""
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
    def _goal_difference_multiplier(self, goal_diff: int) -> float:
        """
        Gol farkına göre çarpan (World Football Elo formülü)
        Büyük gol farkları daha fazla rating değişikliği yaratır
        """
        if goal_diff <= 1:
            return 1.0
        elif goal_diff == 2:
            return 1.5
        else:
            return (11 + goal_diff) / 8
    
    def _dynamic_k_factor(self, match_importance: str = 'league') -> float:
        """Maç önemine göre K-faktör"""
        importance_weights = {
            'friendly': 0.5,
            'league': 1.0,
            'cup': 1.1,
            'european': 1.2,
            'final': 1.4,
            'world_cup': 1.6
        }
        return self.k_base * importance_weights.get(match_importance, 1.0)
    
    def update(self, home_team: str, away_team: str,
               home_goals: int, away_goals: int,
               match_importance: str = 'league') -> Tuple[float, float]:
        """Rating güncelle ve değişimi döndür"""
        
        # Current ratings (home_advantage ekleniyor)
        home_rating = self.get_rating(home_team) + self.home_advantage
        away_rating = self.get_rating(away_team)
        
        # Expected scores
        home_expected = self._expected_score(home_rating, away_rating)
        away_expected = 1 - home_expected
        
        # Actual scores (1=win, 0.5=draw, 0=loss)
        if home_goals > away_goals:
            home_actual, away_actual = 1.0, 0.0
        elif home_goals == away_goals:
            home_actual, away_actual = 0.5, 0.5
        else:
            home_actual, away_actual = 0.0, 1.0
        
        # K-factor and goal difference
        k = self._dynamic_k_factor(match_importance)
        goal_diff = abs(home_goals - away_goals)
        multiplier = self._goal_difference_multiplier(goal_diff)
        
        # Rating changes
        home_change = k * multiplier * (home_actual - home_expected)
        away_change = k * multiplier * (away_actual - away_expected)
        
        # Update
        self.ratings[home_team] = self.get_rating(home_team) + home_change
        self.ratings[away_team] = self.get_rating(away_team) + away_change
        
        # Log history
        self.history.append({
            'home_team': home_team,
            'away_team': away_team,
            'home_rating_before': self.get_rating(home_team) - home_change,
            'home_rating_after': self.get_rating(home_team),
            'away_rating_before': self.get_rating(away_team) - away_change,
            'away_rating_after': self.get_rating(away_team)
        })
        
        return home_change, away_change
    
    def season_regression(self, mean_rating: float = 1500, 
                          regression_factor: float = 0.3):
        """
        Sezon başı regresyon
        Tüm takımları ortalamaya doğru çek
        """
        for team in self.ratings:
            current = self.ratings[team]
            self.ratings[team] = current + regression_factor * (mean_rating - current)
    
    def predict_match(self, home_team: str, away_team: str) -> Dict:
        """Maç tahmini yap"""
        
        home_rating = self.get_rating(home_team) + self.home_advantage
        away_rating = self.get_rating(away_team)
        
        home_win_prob = self._expected_score(home_rating, away_rating)
        
        # Draw probability (empirik formül)
        rating_diff = abs(home_rating - away_rating)
        draw_prob = 0.28 * np.exp(-rating_diff / 400)
        
        # Normalize
        home_prob = home_win_prob * (1 - draw_prob)
        away_prob = (1 - home_win_prob) * (1 - draw_prob)
        
        return {
            'H': home_prob,
            'D': draw_prob,
            'A': away_prob,
            'home_rating': home_rating,
            'away_rating': away_rating,
            'rating_difference': home_rating - away_rating
        }
```

---

## 3. Makine Öğrenmesi Derinlemesine

### 3.1 Gelişmiş Feature Engineering

```python
class AdvancedFeatureEngineer:
    """
    Kapsamlı feature engineering pipeline
    """
    
    def __init__(self):
        self.feature_functions = [
            self._form_features,
            self._h2h_features,
            self._venue_features,
            self._calendar_features,
            self._momentum_features,
            self._xg_features,
            self._odds_features,
            self._market_features
        ]
    
    def create_all_features(self, match: Dict, 
                           home_team_data: pd.DataFrame,
                           away_team_data: pd.DataFrame) -> Dict:
        """Tüm feature'ları oluştur"""
        
        features = {}
        for func in self.feature_functions:
            new_features = func(match, home_team_data, away_team_data)
            features.update(new_features)
        
        return features
    
    def _form_features(self, match: Dict, home_data: pd.DataFrame, 
                       away_data: pd.DataFrame) -> Dict:
        """Form bazlı feature'lar"""
        
        windows = [3, 5, 10]
        features = {}
        
        for w in windows:
            # Son w maç
            home_last = home_data.tail(w)
            away_last = away_data.tail(w)
            
            # Temel metrikler
            features[f'home_points_L{w}'] = home_last['points'].sum()
            features[f'away_points_L{w}'] = away_last['points'].sum()
            features[f'home_goals_scored_L{w}'] = home_last['goals_for'].mean()
            features[f'away_goals_scored_L{w}'] = away_last['goals_for'].mean()
            features[f'home_goals_conceded_L{w}'] = home_last['goals_against'].mean()
            features[f'away_goals_conceded_L{w}'] = away_last['goals_against'].mean()
            
            # Streak (üst üste sonuçlar)
            features[f'home_win_streak'] = self._calc_streak(home_data, 'W')
            features[f'home_unbeaten_streak'] = self._calc_streak(home_data, ['W', 'D'])
            features[f'away_win_streak'] = self._calc_streak(away_data, 'W')
            
            # Ortalamadan sapma
            features[f'home_goals_vs_avg_L{w}'] = (
                home_last['goals_for'].mean() - home_data['goals_for'].mean()
            )
            
        return features
    
    def _momentum_features(self, match: Dict, home_data: pd.DataFrame,
                          away_data: pd.DataFrame) -> Dict:
        """Momentum ve trend feature'ları"""
        
        features = {}
        
        # Form slope (lineer regresyon)
        from scipy.stats import linregress
        
        if len(home_data) >= 5:
            home_points = home_data.tail(10)['points'].values
            x = np.arange(len(home_points))
            slope, _, _, _, _ = linregress(x, home_points)
            features['home_form_slope'] = slope
        else:
            features['home_form_slope'] = 0
            
        if len(away_data) >= 5:
            away_points = away_data.tail(10)['points'].values
            x = np.arange(len(away_points))
            slope, _, _, _, _ = linregress(x, away_points)
            features['away_form_slope'] = slope
        else:
            features['away_form_slope'] = 0
        
        # xG trend
        features['home_xg_trend'] = self._calc_trend(home_data['xg'].tail(5))
        features['away_xg_trend'] = self._calc_trend(away_data['xg'].tail(5))
        
        # Performance vs xG (over/underperformance)
        home_recent = home_data.tail(10)
        features['home_xg_overperformance'] = (
            home_recent['goals_for'].mean() - home_recent['xg'].mean()
        )
        
        away_recent = away_data.tail(10)
        features['away_xg_overperformance'] = (
            away_recent['goals_for'].mean() - away_recent['xg'].mean()
        )
        
        # Volatility (tutarsızlık)
        features['home_volatility'] = home_data['points'].tail(10).std()
        features['away_volatility'] = away_data['points'].tail(10).std()
        
        return features
    
    def _xg_features(self, match: Dict, home_data: pd.DataFrame,
                     away_data: pd.DataFrame) -> Dict:
        """Expected Goals feature'ları"""
        
        features = {}
        
        # xG averages
        features['home_xg_avg'] = home_data['xg'].tail(10).mean()
        features['away_xg_avg'] = away_data['xg'].tail(10).mean()
        features['home_xga_avg'] = home_data['xg_against'].tail(10).mean()
        features['away_xga_avg'] = away_data['xg_against'].tail(10).mean()
        
        # xG ratios
        features['home_xg_ratio'] = features['home_xg_avg'] / (features['home_xga_avg'] + 0.1)
        features['away_xg_ratio'] = features['away_xg_avg'] / (features['away_xga_avg'] + 0.1)
        
        # xG difference (predictor of match outcome)
        features['xg_diff'] = features['home_xg_avg'] - features['away_xg_avg']
        
        # Shot quality (xG per shot)
        features['home_shot_quality'] = home_data['xg'].sum() / (home_data['shots'].sum() + 1)
        features['away_shot_quality'] = away_data['xg'].sum() / (away_data['shots'].sum() + 1)
        
        return features
    
    def _odds_features(self, match: Dict, home_data: pd.DataFrame,
                       away_data: pd.DataFrame) -> Dict:
        """Bahis oranları feature'ları"""
        
        odds = match.get('odds', {})
        if not odds:
            return {}
            
        features = {}
        
        # Implied probabilities
        if 'home' in odds and 'draw' in odds and 'away' in odds:
            total_implied = 1/odds['home'] + 1/odds['draw'] + 1/odds['away']
            
            features['implied_home_prob'] = (1/odds['home']) / total_implied
            features['implied_draw_prob'] = (1/odds['draw']) / total_implied
            features['implied_away_prob'] = (1/odds['away']) / total_implied
            
            # Overround (bookmaker margin)
            features['overround'] = total_implied - 1
            
        # Odds movement (if available)
        if 'opening_odds' in match and 'current_odds' in match:
            features['home_odds_movement'] = (
                match['current_odds']['home'] - match['opening_odds']['home']
            )
            features['away_odds_movement'] = (
                match['current_odds']['away'] - match['opening_odds']['away']
            )
            
        return features
    
    def _calc_trend(self, series: pd.Series) -> float:
        """Lineer trend hesapla"""
        if len(series) < 2:
            return 0
        x = np.arange(len(series))
        slope, _, _, _, _ = linregress(x, series.values)
        return slope
    
    def _calc_streak(self, data: pd.DataFrame, result_types) -> int:
        """Streak hesapla"""
        if isinstance(result_types, str):
            result_types = [result_types]
            
        streak = 0
        for result in data['result'].iloc[::-1]:
            if result in result_types:
                streak += 1
            else:
                break
        return streak
```

### 3.2 XGBoost Hyperparameter Optimization

```python
import optuna
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import log_loss

class XGBoostOptimizer:
    """
    Bayesian optimization ile XGBoost hyperparameter tuning
    """
    
    def __init__(self, n_trials=200, cv_splits=5):
        self.n_trials = n_trials
        self.cv_splits = cv_splits
        self.best_params = None
        self.study = None
        
    def objective(self, trial, X, y):
        """Optuna objective function"""
        
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 100, 500),
            'max_depth': trial.suggest_int('max_depth', 3, 10),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'colsample_bylevel': trial.suggest_float('colsample_bylevel', 0.6, 1.0),
            'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
            'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
            'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True),
            'gamma': trial.suggest_float('gamma', 1e-8, 1.0, log=True),
            'scale_pos_weight': trial.suggest_float('scale_pos_weight', 0.5, 2.0)
        }
        
        # Time series cross-validation
        tscv = TimeSeriesSplit(n_splits=self.cv_splits)
        scores = []
        
        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            model = XGBClassifier(**params, use_label_encoder=False, 
                                  eval_metric='mlogloss', random_state=42)
            
            model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                early_stopping_rounds=50,
                verbose=False
            )
            
            preds = model.predict_proba(X_val)
            score = log_loss(y_val, preds)
            scores.append(score)
        
        return np.mean(scores)
    
    def optimize(self, X, y):
        """Optimizasyonu çalıştır"""
        
        self.study = optuna.create_study(direction='minimize')
        self.study.optimize(
            lambda trial: self.objective(trial, X, y),
            n_trials=self.n_trials,
            show_progress_bar=True
        )
        
        self.best_params = self.study.best_params
        
        return {
            'best_params': self.best_params,
            'best_score': self.study.best_value,
            'optimization_history': self.study.trials_dataframe()
        }
    
    def get_feature_importance(self, X, y) -> pd.DataFrame:
        """Optimized model ile feature importance"""
        
        model = XGBClassifier(**self.best_params, use_label_encoder=False)
        model.fit(X, y)
        
        importance = pd.DataFrame({
            'feature': X.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return importance
```

---

## 4. LLM Mühendisliği

### 4.1 Structured Output Prompting

```python
ANALYSIS_PROMPT = """
You are an expert football analyst. Analyze this upcoming Premier League match.

## Match Information
**{home_team}** vs **{away_team}**
**Date:** {match_date}
**Venue:** {venue}

## Data Available
### Form (Last 5 matches)
- {home_team}: {home_form} ({home_points}/15 points)
- {away_team}: {away_form} ({away_points}/15 points)

### Head-to-Head (Last 5 meetings)
{h2h_summary}

### Key Statistics
| Metric | {home_team} | {away_team} |
|--------|-------------|-------------|
| xG/Match | {home_xg} | {away_xg} |
| Goals/Match | {home_goals} | {away_goals} |
| Clean Sheets | {home_cs} | {away_cs} |

### Injuries/Suspensions
{injuries_summary}

### Recent News
{news_summary}

## Model Predictions
{model_predictions}

## Your Task
Analyze all factors and provide your assessment. Return ONLY valid JSON:

```json
{{
    "analysis": {{
        "form_assessment": "string (2-3 sentences)",
        "tactical_factors": "string (2-3 sentences)",
        "key_battle": "string (1 sentence describing key matchup)",
        "x_factor": "string (1 unexpected factor that could decide the match)"
    }},
    "probability_adjustments": {{
        "home_win": float (-0.10 to 0.10),
        "draw": float (-0.10 to 0.10),
        "away_win": float (-0.10 to 0.10)
    }},
    "confidence": float (0.0 to 1.0),
    "reasoning": "string (1-2 sentences explaining your adjustments)",
    "risk_level": "low" | "medium" | "high",
    "betting_insight": "string (1 sentence on value opportunity if any)"
}}
```
"""

class StructuredLLMAnalyzer:
    """
    Structured output ile LLM analizi
    """
    
    def __init__(self, model='claude-3-sonnet-20240229'):
        self.client = anthropic.Anthropic()
        self.model = model
        
    async def analyze_match(self, match_data: Dict) -> Dict:
        """Maç analizi yap"""
        
        prompt = ANALYSIS_PROMPT.format(**match_data)
        
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse JSON
        content = response.content[0].text
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        
        if json_match:
            return json.loads(json_match.group(1))
        else:
            # Try direct JSON parse
            return json.loads(content)
    
    def validate_adjustments(self, adjustments: Dict) -> bool:
        """Adjustment'ların geçerliliğini kontrol et"""
        
        # Sum should be close to 0 (probability conservation)
        total = sum(adjustments.values())
        if abs(total) > 0.05:
            return False
            
        # Each adjustment within bounds
        for val in adjustments.values():
            if abs(val) > 0.10:
                return False
                
        return True
```

### 4.2 Multi-Model Consensus

```python
class LLMConsensusSystem:
    """
    Birden fazla LLM'den konsensüs al
    """
    
    def __init__(self):
        self.models = {
            'claude': ClaudeLLM('claude-3-sonnet-20240229'),
            'gpt4': GPT4LLM('gpt-4-turbo-preview'),
            'gemini': GeminiLLM('gemini-pro')
        }
        
    async def get_consensus(self, match_data: Dict) -> Dict:
        """Tüm modellerden analiz al ve birleştir"""
        
        # Parallel execution
        tasks = [
            model.analyze(match_data) 
            for model in self.models.values()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        valid_results = []
        for name, result in zip(self.models.keys(), results):
            if not isinstance(result, Exception):
                result['model'] = name
                valid_results.append(result)
        
        if len(valid_results) < 2:
            raise ValueError("Insufficient valid LLM responses")
        
        # Calculate consensus
        return self._compute_consensus(valid_results)
    
    def _compute_consensus(self, results: List[Dict]) -> Dict:
        """Konsensüs hesapla"""
        
        # Weighted average of probability adjustments
        # Weight by confidence
        total_weight = sum(r['confidence'] for r in results)
        
        consensus_adjustments = {'home_win': 0, 'draw': 0, 'away_win': 0}
        
        for result in results:
            weight = result['confidence'] / total_weight
            for outcome in consensus_adjustments:
                consensus_adjustments[outcome] += (
                    weight * result['probability_adjustments'][outcome]
                )
        
        # Agreement score
        adjustments_matrix = np.array([
            [r['probability_adjustments'][o] for o in ['home_win', 'draw', 'away_win']]
            for r in results
        ])
        
        agreement = 1 - np.mean(np.std(adjustments_matrix, axis=0))
        
        # Combine reasoning
        reasonings = [f"[{r['model']}]: {r['reasoning']}" for r in results]
        
        return {
            'consensus_adjustments': consensus_adjustments,
            'agreement_score': agreement,
            'individual_results': results,
            'combined_reasoning': '\n'.join(reasonings),
            'confidence': np.mean([r['confidence'] for r in results]) * agreement
        }
```

---

## 5. Betting Matematiği

### 5.1 Gelişmiş Kelly Criterion

```python
class AdvancedKellyCalculator:
    """
    Fractional Kelly ve risk-adjusted stake hesaplama
    """
    
    def __init__(self, kelly_fraction: float = 0.25, 
                 max_stake: float = 0.05,
                 min_edge: float = 0.02):
        self.kelly_fraction = kelly_fraction
        self.max_stake = max_stake
        self.min_edge = min_edge
        
    def calculate_stake(self, predicted_prob: float, 
                       odds: float,
                       confidence: float = 1.0) -> Dict:
        """Stake hesapla"""
        
        # Implied probability
        implied_prob = 1 / odds
        
        # Edge
        edge = predicted_prob - implied_prob
        
        if edge < self.min_edge:
            return {'stake': 0, 'edge': edge, 'reason': 'Insufficient edge'}
        
        # Full Kelly
        b = odds - 1  # Net odds
        q = 1 - predicted_prob
        full_kelly = (predicted_prob * b - q) / b
        
        # Fractional Kelly (risk adjustment)
        fractional_kelly = full_kelly * self.kelly_fraction
        
        # Confidence adjustment
        adjusted_kelly = fractional_kelly * confidence
        
        # Apply maximum stake limit
        final_stake = min(adjusted_kelly, self.max_stake)
        final_stake = max(0, final_stake)  # No negative stakes
        
        # Expected value
        ev = predicted_prob * (odds - 1) - (1 - predicted_prob)
        
        return {
            'stake': final_stake,
            'full_kelly': full_kelly,
            'fractional_kelly': fractional_kelly,
            'edge': edge,
            'expected_value': ev,
            'implied_probability': implied_prob,
            'confidence': confidence
        }
    
    def calculate_portfolio(self, bets: List[Dict], 
                           bankroll: float) -> List[Dict]:
        """
        Çoklu bahis için portfolio optimizasyonu
        Overlapping events için korelasyon düzeltmesi
        """
        
        # Calculate individual stakes
        stakes = []
        for bet in bets:
            stake_info = self.calculate_stake(
                bet['predicted_prob'],
                bet['odds'],
                bet.get('confidence', 1.0)
            )
            stake_info['bet'] = bet
            stakes.append(stake_info)
        
        # Filter zero stakes
        stakes = [s for s in stakes if s['stake'] > 0]
        
        # Total stakes check (shouldn't exceed 50% of bankroll)
        total_stake_pct = sum(s['stake'] for s in stakes)
        
        if total_stake_pct > 0.5:
            # Scale down proportionally
            scale_factor = 0.5 / total_stake_pct
            for s in stakes:
                s['stake'] *= scale_factor
                s['scaled'] = True
        
        # Convert to absolute amounts
        for s in stakes:
            s['amount'] = s['stake'] * bankroll
            
        return stakes
```

### 5.2 Value Bet Detection

```python
class ValueBetDetector:
    """
    Value bet tespiti ve analizi
    """
    
    def __init__(self, min_edge: float = 0.03, 
                 min_confidence: float = 0.6):
        self.min_edge = min_edge
        self.min_confidence = min_confidence
        
    def detect(self, prediction: Dict, odds: Dict) -> List[Dict]:
        """Value bet'leri tespit et"""
        
        value_bets = []
        
        outcomes = [
            ('H', '1X2', 'home'),
            ('D', '1X2', 'draw'),
            ('A', '1X2', 'away')
        ]
        
        for outcome_key, market, odds_key in outcomes:
            pred_prob = prediction['probabilities'][outcome_key]
            market_odds = odds.get(odds_key, 0)
            
            if market_odds <= 1:
                continue
                
            implied_prob = 1 / market_odds
            edge = pred_prob - implied_prob
            
            if edge >= self.min_edge:
                # Calculate value metrics
                expected_return = pred_prob * market_odds - 1
                sharpe = expected_return / np.sqrt(pred_prob * (1 - pred_prob))
                
                value_bets.append({
                    'outcome': outcome_key,
                    'market': market,
                    'predicted_prob': pred_prob,
                    'implied_prob': implied_prob,
                    'odds': market_odds,
                    'edge': edge,
                    'expected_return': expected_return,
                    'sharpe_ratio': sharpe,
                    'confidence': prediction.get('confidence', 1.0),
                    'recommendation': self._get_recommendation(edge, sharpe)
                })
        
        # Sort by edge
        value_bets.sort(key=lambda x: x['edge'], reverse=True)
        
        return value_bets
    
    def _get_recommendation(self, edge: float, sharpe: float) -> str:
        """Bahis önerisi"""
        
        if edge >= 0.10 and sharpe >= 0.5:
            return 'STRONG_BET'
        elif edge >= 0.05 and sharpe >= 0.3:
            return 'MODERATE_BET'
        elif edge >= self.min_edge:
            return 'SMALL_BET'
        else:
            return 'NO_BET'
```

### 5.3 Bankroll Management

```python
class BankrollManager:
    """
    Kapsamlı bankroll yönetimi
    """
    
    def __init__(self, initial_bankroll: float,
                 risk_level: str = 'moderate'):
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.risk_level = risk_level
        self.history = []
        
        self.risk_params = {
            'conservative': {
                'kelly_fraction': 0.15,
                'max_stake': 0.02,
                'max_daily_loss': 0.05,
                'target_monthly_growth': 0.03
            },
            'moderate': {
                'kelly_fraction': 0.25,
                'max_stake': 0.05,
                'max_daily_loss': 0.10,
                'target_monthly_growth': 0.08
            },
            'aggressive': {
                'kelly_fraction': 0.40,
                'max_stake': 0.10,
                'max_daily_loss': 0.20,
                'target_monthly_growth': 0.15
            }
        }
        
    def get_max_stake(self) -> float:
        """Mevcut duruma göre maksimum stake"""
        
        params = self.risk_params[self.risk_level]
        base_max = params['max_stake']
        
        # Drawdown'a göre ayarla
        current_drawdown = self.get_drawdown()
        
        if current_drawdown > 0.15:
            # Büyük drawdown - stake'i azalt
            return base_max * 0.5
        elif current_drawdown > 0.10:
            return base_max * 0.75
        else:
            return base_max
    
    def record_bet(self, stake: float, odds: float, 
                   won: bool, bet_info: Dict = None):
        """Bahis sonucu kaydet"""
        
        if won:
            profit = stake * (odds - 1)
        else:
            profit = -stake
            
        self.current_bankroll += profit
        
        self.history.append({
            'timestamp': datetime.now(),
            'stake': stake,
            'odds': odds,
            'won': won,
            'profit': profit,
            'bankroll_after': self.current_bankroll,
            'info': bet_info
        })
    
    def get_statistics(self) -> Dict:
        """Performans istatistikleri"""
        
        if not self.history:
            return {}
            
        df = pd.DataFrame(self.history)
        
        return {
            'total_bets': len(df),
            'won': df['won'].sum(),
            'lost': (~df['won']).sum(),
            'win_rate': df['won'].mean(),
            'total_profit': df['profit'].sum(),
            'roi': (self.current_bankroll - self.initial_bankroll) / self.initial_bankroll,
            'max_drawdown': self.get_max_drawdown(),
            'sharpe_ratio': self._calculate_sharpe(),
            'average_odds_won': df[df['won']]['odds'].mean() if df['won'].any() else 0,
            'daily_roi': df.groupby(df['timestamp'].dt.date)['profit'].sum().mean() / self.initial_bankroll
        }
    
    def get_drawdown(self) -> float:
        """Mevcut drawdown"""
        
        if not self.history:
            return 0
            
        peak = max(h['bankroll_after'] for h in self.history)
        peak = max(peak, self.initial_bankroll)
        
        return (peak - self.current_bankroll) / peak
    
    def get_max_drawdown(self) -> float:
        """Maksimum drawdown"""
        
        if not self.history:
            return 0
            
        bankrolls = [self.initial_bankroll] + [h['bankroll_after'] for h in self.history]
        peak = bankrolls[0]
        max_dd = 0
        
        for br in bankrolls:
            if br > peak:
                peak = br
            dd = (peak - br) / peak
            max_dd = max(max_dd, dd)
            
        return max_dd
    
    def _calculate_sharpe(self) -> float:
        """Sharpe ratio hesapla"""
        
        if len(self.history) < 10:
            return 0
            
        profits = [h['profit'] for h in self.history]
        mean_profit = np.mean(profits)
        std_profit = np.std(profits)
        
        if std_profit == 0:
            return 0
            
        # Annualized (assuming 500 bets/year)
        return (mean_profit / std_profit) * np.sqrt(500)
```

---

## 6. Veri Bilimi Pipeline

### 6.1 End-to-End Pipeline

```python
class MatchPredictionPipeline:
    """
    Tam tahmin pipeline'ı
    """
    
    def __init__(self, config: Dict):
        # Initialize components
        self.data_fetcher = DataFetcher(config['data_sources'])
        self.feature_engineer = AdvancedFeatureEngineer()
        self.models = self._load_models(config['models'])
        self.ensemble = EnsemblePredictor(config['ensemble'])
        self.llm_analyzer = StructuredLLMAnalyzer()
        self.value_detector = ValueBetDetector()
        self.calibrator = ProbabilityCalibrator()
        
    async def predict(self, match: Dict) -> MatchPrediction:
        """Maç tahmini yap"""
        
        # 1. Fetch data
        home_data = await self.data_fetcher.get_team_data(match['home_team'])
        away_data = await self.data_fetcher.get_team_data(match['away_team'])
        news_data = await self.data_fetcher.get_news(match)
        odds_data = await self.data_fetcher.get_odds(match['match_id'])
        
        # 2. Feature engineering
        features = self.feature_engineer.create_all_features(
            match, home_data, away_data
        )
        
        # 3. Model predictions
        model_predictions = {}
        for name, model in self.models.items():
            pred = model.predict_proba(features)
            model_predictions[name] = pred
        
        # 4. Ensemble
        ensemble_pred = self.ensemble.combine(model_predictions)
        
        # 5. Calibration
        calibrated_pred = self.calibrator.calibrate(ensemble_pred)
        
        # 6. LLM analysis
        llm_result = await self.llm_analyzer.analyze_match({
            **match,
            'model_predictions': calibrated_pred,
            'news_summary': news_data
        })
        
        # 7. Apply LLM adjustments
        final_pred = self._apply_adjustments(
            calibrated_pred, 
            llm_result['probability_adjustments']
        )
        
        # 8. Value bet detection
        value_bets = self.value_detector.detect(
            {'probabilities': final_pred},
            odds_data
        )
        
        return MatchPrediction(
            match_id=match['match_id'],
            probabilities=final_pred,
            model_breakdown=model_predictions,
            ensemble_probabilities=ensemble_pred,
            calibrated_probabilities=calibrated_pred,
            llm_analysis=llm_result,
            value_bets=value_bets,
            confidence=llm_result['confidence'],
            timestamp=datetime.now()
        )
```

---

## 7. Performans Optimizasyonu

### 7.1 Model Caching ve Lazy Loading

```python
from functools import lru_cache
import pickle
import hashlib

class ModelCache:
    """Model ve prediction caching"""
    
    def __init__(self, cache_dir: str = '/tmp/model_cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.memory_cache = {}
        
    def get_or_compute(self, key: str, compute_fn, ttl_seconds: int = 3600):
        """Cache'den al veya hesapla"""
        
        cache_key = hashlib.md5(key.encode()).hexdigest()
        
        # Memory cache check
        if cache_key in self.memory_cache:
            cached = self.memory_cache[cache_key]
            if time.time() - cached['timestamp'] < ttl_seconds:
                return cached['value']
        
        # Disk cache check
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                cached = pickle.load(f)
            if time.time() - cached['timestamp'] < ttl_seconds:
                self.memory_cache[cache_key] = cached
                return cached['value']
        
        # Compute
        value = compute_fn()
        
        # Store
        cached = {'value': value, 'timestamp': time.time()}
        self.memory_cache[cache_key] = cached
        with open(cache_file, 'wb') as f:
            pickle.dump(cached, f)
        
        return value
```

---

## 8. Araştırma Protokolleri

### 8.1 Experiment Tracking

```yaml
# mlflow config
experiment:
  name: "football-predictor"
  tracking_uri: "sqlite:///mlflow.db"
  
  metrics_to_log:
    - accuracy
    - log_loss
    - brier_score
    - rps
    - roi
    
  artifacts:
    - model_weights
    - feature_importance
    - calibration_curve
    - confusion_matrix
```

### 8.2 Backtesting Protocol

```python
class BacktestingProtocol:
    """
    Standart backtesting protokolü
    """
    
    def __init__(self, start_date: str, end_date: str, 
                 initial_bankroll: float = 1000):
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.initial_bankroll = initial_bankroll
        
    def run(self, model, data: pd.DataFrame) -> BacktestResults:
        """Backtest çalıştır"""
        
        # Filter to date range
        mask = (data['match_date'] >= self.start_date) & \
               (data['match_date'] <= self.end_date)
        test_data = data[mask].sort_values('match_date')
        
        results = []
        bankroll = self.initial_bankroll
        
        for _, match in test_data.iterrows():
            # Get prediction
            prediction = model.predict(match)
            
            # Simulate betting
            bet_result = self._simulate_bet(
                prediction, 
                match['odds'],
                match['result'],
                bankroll
            )
            
            bankroll += bet_result['profit']
            
            results.append({
                'match_date': match['match_date'],
                'prediction': prediction,
                'actual': match['result'],
                'profit': bet_result['profit'],
                'bankroll': bankroll,
                **bet_result
            })
        
        return BacktestResults(
            data=pd.DataFrame(results),
            final_bankroll=bankroll,
            roi=(bankroll - self.initial_bankroll) / self.initial_bankroll,
            metrics=self._calculate_metrics(results)
        )
```

---

## 📚 Kaynaklar

### Akademik
- Dixon & Coles (1997) - "Modelling Association Football Scores"
- Hvattum & Arntzen (2010) - "Using ELO ratings for match result prediction"
- Constantinou et al. (2012) - "Profiting from an inefficient market"

### Kütüphaneler
```bash
pip install scikit-learn xgboost lightgbm
pip install torch torchvision
pip install optuna mlflow
pip install anthropic openai
pip install pandas numpy scipy
```

---

**Son Güncelleme**: 2026-01-04
**Versiyon**: 3.0
