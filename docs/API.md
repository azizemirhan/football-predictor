# 📡 API Dokümantasyonu

> **Football Predictor Pro - RESTful API Reference**

---

## 📋 İçindekiler

1. [Genel Bilgiler](#1-genel-bilgiler)
2. [Kimlik Doğrulama](#2-kimlik-doğrulama)
3. [Matches API](#3-matches-api)
4. [Teams API](#4-teams-api)
5. [Predictions API](#5-predictions-api)
6. [Odds API](#6-odds-api)
7. [Value Bets API](#7-value-bets-api)
8. [Analytics API](#8-analytics-api)
9. [WebSocket Events](#9-websocket-events)
10. [Hata Kodları](#10-hata-kodları)

---

## 1. Genel Bilgiler

### 1.1 Base URL

```
Production:  https://api.footballpredictor.com/v1
Development: http://localhost:8000/api/v1
```

### 1.2 Response Format

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2025-01-03T15:00:00Z",
    "request_id": "req_abc123",
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 100
    }
  }
}
```

### 1.3 Hata Yanıtı

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid date format",
    "details": { "field": "date_from" }
  }
}
```

---

## 2. Kimlik Doğrulama

### 2.1 Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com"
    },
    "session": {
      "access_token": "eyJhbGc...",
      "refresh_token": "refresh_token",
      "expires_at": 1704153600
    }
  }
}
```

### 2.2 Header'da Token Kullanımı

```http
Authorization: Bearer <access_token>
```

---

## 3. Matches API

### 3.1 List Matches

```http
GET /api/v1/matches
```

**Query Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `status` | string | `scheduled`, `live`, `finished` | `all` |
| `league` | string | Lig slug'ı | - |
| `team_id` | integer | Takım ID | - |
| `date_from` | date | YYYY-MM-DD | - |
| `date_to` | date | YYYY-MM-DD | - |
| `page` | integer | Sayfa | 1 |
| `per_page` | integer | Kayıt/sayfa (max: 100) | 20 |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": 12345,
      "home_team": {
        "id": 1,
        "name": "Liverpool",
        "short_name": "LIV",
        "logo_url": "https://..."
      },
      "away_team": {
        "id": 2,
        "name": "Arsenal",
        "short_name": "ARS",
        "logo_url": "https://..."
      },
      "league": "Premier League",
      "match_date": "2025-01-05T15:00:00Z",
      "status": "scheduled",
      "venue": "Anfield",
      "matchday": 20
    }
  ]
}
```

### 3.2 Get Match

```http
GET /api/v1/matches/{id}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": 12345,
    "home_team": {
      "id": 1,
      "name": "Liverpool",
      "form": ["W", "W", "D", "W", "L"]
    },
    "away_team": {
      "id": 2,
      "name": "Arsenal",
      "form": ["W", "D", "W", "W", "W"]
    },
    "match_date": "2025-01-05T15:00:00Z",
    "status": "scheduled",
    "venue": "Anfield",
    "referee": "Michael Oliver",
    "head_to_head": {
      "total_matches": 10,
      "home_wins": 4,
      "draws": 3,
      "away_wins": 3
    }
  }
}
```

### 3.3 Get Match Statistics

```http
GET /api/v1/matches/{id}/stats
```

**Response:**

```json
{
  "success": true,
  "data": {
    "match_id": 12345,
    "home_stats": {
      "possession": 58.5,
      "shots": 15,
      "shots_on_target": 7,
      "corners": 8,
      "fouls": 11,
      "yellow_cards": 2,
      "xg": 2.34
    },
    "away_stats": {
      "possession": 41.5,
      "shots": 10,
      "shots_on_target": 4,
      "corners": 4,
      "fouls": 14,
      "yellow_cards": 3,
      "xg": 1.12
    }
  }
}
```

### 3.4 Get Match Lineups

```http
GET /api/v1/matches/{id}/lineups
```

### 3.5 Get Live Matches

```http
GET /api/v1/matches/live
```

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": 12345,
      "home_team": "Liverpool",
      "away_team": "Arsenal",
      "home_score": 2,
      "away_score": 1,
      "minute": 67,
      "status": "live"
    }
  ]
}
```

---

## 4. Teams API

### 4.1 List Teams

```http
GET /api/v1/teams
```

### 4.2 Get Team

```http
GET /api/v1/teams/{id}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Liverpool",
    "short_name": "LIV",
    "league": "Premier League",
    "stadium": "Anfield",
    "manager": "Arne Slot",
    "current_season": {
      "position": 1,
      "played": 19,
      "won": 13,
      "drawn": 4,
      "lost": 2,
      "points": 43
    },
    "form": ["W", "W", "D", "W", "L"],
    "elo_rating": 1892.5
  }
}
```

### 4.3 Get Team Matches

```http
GET /api/v1/teams/{id}/matches
```

### 4.4 Get Team Statistics

```http
GET /api/v1/teams/{id}/stats?season=2024-25
```

---

## 5. Predictions API

### 5.1 Get Match Prediction

```http
GET /api/v1/predictions/match/{match_id}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "match_id": 12345,
    "home_team": "Liverpool",
    "away_team": "Arsenal",
    "prediction": {
      "home_win_prob": 0.452,
      "draw_prob": 0.281,
      "away_win_prob": 0.267,
      "expected_home_goals": 1.85,
      "expected_away_goals": 1.12,
      "most_likely_score": "2-1",
      "confidence": 0.68
    },
    "model_breakdown": {
      "poisson": {
        "home_win": 0.44,
        "draw": 0.28,
        "away_win": 0.28,
        "weight": 0.25
      },
      "elo": {
        "home_win": 0.48,
        "draw": 0.26,
        "away_win": 0.26,
        "weight": 0.20
      },
      "xgboost": {
        "home_win": 0.46,
        "draw": 0.29,
        "away_win": 0.25,
        "weight": 0.30
      },
      "llm_adjusted": {
        "home_win": 0.45,
        "draw": 0.28,
        "away_win": 0.27,
        "weight": 0.25
      }
    },
    "factors": {
      "home_advantage": "+8.5%",
      "form_difference": "+5.2%",
      "h2h_record": "+2.1%",
      "injury_impact": "-3.2%"
    },
    "reasoning": "Liverpool's strong home form gives them the edge."
  }
}
```

### 5.2 Get Today's Predictions

```http
GET /api/v1/predictions/today
```

### 5.3 Get Score Predictions

```http
GET /api/v1/predictions/match/{match_id}/scores
```

**Response:**

```json
{
  "success": true,
  "data": {
    "score_matrix": {
      "0-0": 0.052,
      "1-0": 0.098,
      "2-0": 0.087,
      "1-1": 0.112,
      "2-1": 0.145
    },
    "over_under": {
      "over_0.5": 0.892,
      "over_1.5": 0.723,
      "over_2.5": 0.512,
      "over_3.5": 0.287
    },
    "btts": {
      "yes": 0.623,
      "no": 0.377
    }
  }
}
```

### 5.4 List Predictions

```http
GET /api/v1/predictions
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `date` | date | Tarih |
| `league` | string | Lig |
| `min_confidence` | float | Min güven (0-1) |
| `status` | string | `pending`, `correct`, `incorrect` |

---

## 6. Odds API

### 6.1 Get Match Odds

```http
GET /api/v1/odds/match/{match_id}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "match_id": 12345,
    "last_updated": "2025-01-03T14:55:00Z",
    "markets": {
      "1x2": {
        "bookmakers": [
          {
            "name": "Bet365",
            "home": 2.10,
            "draw": 3.40,
            "away": 3.50
          },
          {
            "name": "William Hill",
            "home": 2.05,
            "draw": 3.45,
            "away": 3.60
          }
        ],
        "best_odds": {
          "home": {"odds": 2.10, "bookmaker": "Bet365"},
          "draw": {"odds": 3.50, "bookmaker": "Pinnacle"},
          "away": {"odds": 3.60, "bookmaker": "William Hill"}
        }
      },
      "over_under": {
        "2.5": {"over": 1.85, "under": 1.95},
        "3.5": {"over": 2.40, "under": 1.55}
      },
      "btts": {
        "yes": 1.72,
        "no": 2.10
      }
    }
  }
}
```

### 6.2 Get Odds Movement

```http
GET /api/v1/odds/match/{match_id}/movement
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `market` | string | Market türü |
| `bookmaker` | string | Bahis şirketi |
| `hours` | integer | Son kaç saat |

**Response:**

```json
{
  "success": true,
  "data": {
    "movements": [
      {"timestamp": "2025-01-03T10:00:00Z", "home": 2.20, "draw": 3.30, "away": 3.40},
      {"timestamp": "2025-01-03T12:00:00Z", "home": 2.15, "draw": 3.35, "away": 3.45},
      {"timestamp": "2025-01-03T14:00:00Z", "home": 2.10, "draw": 3.40, "away": 3.50}
    ],
    "change_percent": {
      "home": -6.7,
      "draw": 4.6,
      "away": 6.1
    }
  }
}
```

---

## 7. Value Bets API

### 7.1 List Value Bets

```http
GET /api/v1/value-bets
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `min_edge` | float | Min edge (örn: 0.05) |
| `min_confidence` | float | Min güven |
| `status` | string | `pending`, `won`, `lost` |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": 8001,
      "match": {
        "id": 12345,
        "home_team": "Liverpool",
        "away_team": "Arsenal",
        "match_date": "2025-01-05T15:00:00Z"
      },
      "selection": "Home Win",
      "market": "1x2",
      "bookmaker": "Bet365",
      "odds": 2.10,
      "predicted_probability": 0.52,
      "implied_probability": 0.476,
      "edge": 0.092,
      "kelly_stake": 0.044,
      "recommended_stake_percent": 2.2,
      "confidence": "high",
      "status": "pending"
    }
  ]
}
```

### 7.2 Get Value Bet Summary

```http
GET /api/v1/value-bets/summary
```

**Response:**

```json
{
  "success": true,
  "data": {
    "today": {
      "total_bets": 5,
      "avg_edge": 0.072
    },
    "week": {
      "total_bets": 23,
      "won": 12,
      "lost": 8,
      "pending": 3,
      "roi": 12.5
    }
  }
}
```

---

## 8. Analytics API

### 8.1 Get Model Performance

```http
GET /api/v1/analytics/performance
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | Model adı |
| `period` | string | `7d`, `30d`, `90d`, `all` |
| `league` | string | Lig filtresi |

**Response:**

```json
{
  "success": true,
  "data": {
    "period": "30d",
    "models": [
      {
        "name": "ensemble",
        "metrics": {
          "accuracy": 0.542,
          "log_loss": 0.948,
          "brier_score": 0.215,
          "rps": 0.198
        },
        "predictions_count": 156,
        "correct_predictions": 85
      }
    ]
  }
}
```

### 8.2 Get ROI Statistics

```http
GET /api/v1/analytics/roi
```

**Response:**

```json
{
  "success": true,
  "data": {
    "period": "30d",
    "starting_bankroll": 1000,
    "current_bankroll": 1085,
    "total_bets": 45,
    "winning_bets": 23,
    "win_rate": 0.511,
    "roi": 8.5,
    "max_drawdown": -12.5,
    "sharpe_ratio": 1.45,
    "by_confidence": {
      "high": {"bets": 15, "roi": 15.2},
      "medium": {"bets": 20, "roi": 5.8},
      "low": {"bets": 10, "roi": -2.1}
    }
  }
}
```

---

## 9. WebSocket Events

### 9.1 Bağlantı

```javascript
const socket = io('wss://api.footballpredictor.com', {
  auth: { token: 'jwt_token' }
});
```

### 9.2 Kanallara Abone Olma

```javascript
// Canlı maçlar
socket.emit('subscribe', { channel: 'matches:live' });

// Belirli maç
socket.emit('subscribe', { channel: 'matches:12345' });

// Value bet alertleri
socket.emit('subscribe', { channel: 'value_bets:alerts' });
```

### 9.3 Event Türleri

**Match Update:**
```javascript
socket.on('match:update', (data) => {
  // { match_id, home_score, away_score, minute, status }
});
```

**Goal:**
```javascript
socket.on('match:goal', (data) => {
  // { match_id, team, scorer, minute, score }
});
```

**Value Bet Alert:**
```javascript
socket.on('value_bet:alert', (data) => {
  // { match_id, selection, odds, edge, confidence }
});
```

**Odds Change:**
```javascript
socket.on('odds:change', (data) => {
  // { match_id, bookmaker, previous, current, change_percent }
});
```

---

## 10. Hata Kodları

### 10.1 HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |

### 10.2 Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Geçersiz parametre |
| `AUTHENTICATION_ERROR` | Geçersiz token |
| `NOT_FOUND` | Kaynak bulunamadı |
| `RATE_LIMIT_EXCEEDED` | Çok fazla istek |

### 10.3 Rate Limiting

| Endpoint | Limit |
|----------|-------|
| `/api/v1/*` | 100 req/min |
| `/api/v1/predictions/*` | 30 req/min |
| WebSocket | 100 msg/min |

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704297600
```

---

## Örnek Kullanım

### cURL

```bash
# Maçları listele
curl -X GET "https://api.footballpredictor.com/v1/matches?status=scheduled" \
  -H "Authorization: Bearer <token>"

# Tahmin al
curl -X GET "https://api.footballpredictor.com/v1/predictions/match/12345" \
  -H "Authorization: Bearer <token>"

# Value bet'leri listele
curl -X GET "https://api.footballpredictor.com/v1/value-bets?min_edge=0.05" \
  -H "Authorization: Bearer <token>"
```

### Python

```python
import requests

headers = {"Authorization": f"Bearer {token}"}

# Maçları al
response = requests.get(
    "https://api.footballpredictor.com/v1/matches",
    params={"status": "scheduled"},
    headers=headers
)
matches = response.json()["data"]

# Tahmin al
response = requests.get(
    f"https://api.footballpredictor.com/v1/predictions/match/12345",
    headers=headers
)
prediction = response.json()["data"]
```

### JavaScript

```javascript
const API_URL = 'https://api.footballpredictor.com/v1';

// Maçları al
const matches = await fetch(`${API_URL}/matches?status=scheduled`, {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Tahmin al
const prediction = await fetch(`${API_URL}/predictions/match/12345`, {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());
```

---

**Son Güncelleme**: 2025-01-03  
**API Version**: 1.0.0