"""
AI Engine FastAPI Application
"""

import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import structlog

from models import (
    PoissonModel, EloModel, XGBoostModel, 
    EnsembleModel, create_default_ensemble
)
from betting import ValueBetCalculator
from features import FeatureEngineer

logger = structlog.get_logger()

# Global model instances
models = {}
value_calculator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - load models on startup"""
    global models, value_calculator
    
    logger.info("loading_models")
    
    # Initialize models
    models["poisson"] = PoissonModel()
    models["elo"] = EloModel()
    models["xgboost"] = XGBoostModel()
    models["ensemble"] = create_default_ensemble()
    
    # Initialize value bet calculator
    value_calculator = ValueBetCalculator()
    
    logger.info("models_loaded", count=len(models))
    
    yield
    
    logger.info("shutting_down")


app = FastAPI(
    title="Football Predictor AI Engine",
    description="AI-powered football match prediction API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================
# Request/Response Models
# ============================

class MatchInput(BaseModel):
    """Input model for match prediction"""
    home_team: str
    away_team: str
    match_id: Optional[str] = None
    features: Optional[Dict[str, float]] = None


class PredictionResponse(BaseModel):
    """Response model for prediction"""
    match_id: Optional[str]
    home_team: str
    away_team: str
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    expected_home_goals: Optional[float]
    expected_away_goals: Optional[float]
    most_likely_score: Optional[str]
    predicted_result: str
    confidence: float
    model: str
    factors: Optional[Dict] = None


class ValueBetResponse(BaseModel):
    """Response model for value bet"""
    match_id: str
    home_team: str
    away_team: str
    selection: str
    market_type: str
    bookmaker: str
    odds: float
    predicted_prob: float
    implied_prob: float
    edge: float
    kelly_fraction: float
    recommended_stake: float
    confidence: float


class ModelInfoResponse(BaseModel):
    """Response model for model info"""
    name: str
    version: str
    is_trained: bool
    last_trained: Optional[datetime]
    training_metrics: Optional[Dict]


class TeamRatingResponse(BaseModel):
    """Response model for team rating"""
    team: str
    elo: float
    attack_strength: Optional[float]
    defense_strength: Optional[float]


# ============================
# Health Endpoints
# ============================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "models_loaded": len(models),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check - are models trained?"""
    trained = {name: model.is_trained for name, model in models.items()}
    return {
        "ready": any(trained.values()),
        "models": trained
    }


# ============================
# Prediction Endpoints
# ============================

@app.post("/predict", response_model=PredictionResponse)
async def predict_match(match: MatchInput, model_name: str = "ensemble"):
    """
    Predict match outcome using specified model.
    
    - **model_name**: One of 'poisson', 'elo', 'xgboost', 'ensemble'
    """
    if model_name not in models:
        raise HTTPException(status_code=400, detail=f"Unknown model: {model_name}")
    
    model = models[model_name]
    
    try:
        prediction = model.predict(match.model_dump())
        return PredictionResponse(**prediction)
    except Exception as e:
        logger.error("prediction_error", model=model_name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/batch", response_model=List[PredictionResponse])
async def predict_batch(matches: List[MatchInput], model_name: str = "ensemble"):
    """Predict multiple matches"""
    if model_name not in models:
        raise HTTPException(status_code=400, detail=f"Unknown model: {model_name}")
    
    model = models[model_name]
    
    predictions = []
    for match in matches:
        try:
            pred = model.predict(match.model_dump())
            predictions.append(PredictionResponse(**pred))
        except Exception as e:
            logger.warning("batch_prediction_error", error=str(e))
            continue
    
    return predictions


@app.post("/predict/all-models")
async def predict_all_models(match: MatchInput):
    """Get predictions from all models for comparison"""
    results = {}
    
    for name, model in models.items():
        try:
            pred = model.predict(match.model_dump())
            results[name] = pred
        except Exception as e:
            results[name] = {"error": str(e)}
    
    return results


# ============================
# Value Bet Endpoints
# ============================

@app.post("/value-bets", response_model=List[ValueBetResponse])
async def find_value_bets(
    prediction: Dict,
    odds: Dict
):
    """Find value bets for a match given prediction and odds"""
    if value_calculator is None:
        raise HTTPException(status_code=500, detail="Value calculator not initialized")
    
    value_bets = value_calculator.find_value_bets(prediction, odds)
    
    return [ValueBetResponse(**vb.to_dict()) for vb in value_bets]


@app.get("/value-bets/settings")
async def get_value_bet_settings():
    """Get current value bet calculator settings"""
    return {
        "min_edge": value_calculator.min_edge,
        "min_odds": value_calculator.min_odds,
        "max_odds": value_calculator.max_odds,
        "kelly_fraction": value_calculator.kelly_fraction,
        "max_stake": value_calculator.max_stake,
        "confidence_threshold": value_calculator.confidence_threshold
    }


# ============================
# Model Management Endpoints
# ============================

@app.get("/models", response_model=List[ModelInfoResponse])
async def list_models():
    """List all available models"""
    return [
        ModelInfoResponse(**model.get_model_info())
        for model in models.values()
    ]


@app.get("/models/{model_name}", response_model=ModelInfoResponse)
async def get_model_info(model_name: str):
    """Get information about a specific model"""
    if model_name not in models:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_name}")
    
    return ModelInfoResponse(**models[model_name].get_model_info())


@app.post("/models/{model_name}/train")
async def train_model(
    model_name: str,
    background_tasks: BackgroundTasks
):
    """Trigger model training (async)"""
    if model_name not in models:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_name}")
    
    # TODO: Add actual training logic
    return {"message": f"Training queued for {model_name}"}


# ============================
# Team Ratings Endpoints
# ============================

@app.get("/ratings", response_model=List[TeamRatingResponse])
async def get_ratings(top_n: int = Query(default=20, le=100)):
    """Get team Elo ratings"""
    if "elo" not in models:
        raise HTTPException(status_code=500, detail="Elo model not available")
    
    elo_model = models["elo"]
    rankings = elo_model.get_rankings(top_n)
    
    # Get Poisson strengths if available
    poisson_model = models.get("poisson")
    
    results = []
    for team, elo in rankings:
        rating = TeamRatingResponse(
            team=team,
            elo=elo,
            attack_strength=poisson_model.attack_strengths.get(team) if poisson_model else None,
            defense_strength=poisson_model.defense_strengths.get(team) if poisson_model else None
        )
        results.append(rating)
    
    return results


@app.get("/ratings/{team}")
async def get_team_rating(team: str):
    """Get rating for a specific team"""
    if "elo" not in models:
        raise HTTPException(status_code=500, detail="Elo model not available")
    
    elo = models["elo"].get_rating(team)
    poisson = models.get("poisson")
    
    return {
        "team": team,
        "elo": elo,
        "attack_strength": poisson.attack_strengths.get(team) if poisson else None,
        "defense_strength": poisson.defense_strengths.get(team) if poisson else None
    }


# ============================
# Score Prediction Endpoints
# ============================

@app.get("/score-matrix")
async def get_score_matrix(
    home_team: str,
    away_team: str,
    max_goals: int = Query(default=6, le=10)
):
    """Get probability matrix for each possible score"""
    if "poisson" not in models:
        raise HTTPException(status_code=500, detail="Poisson model not available")
    
    matrix = models["poisson"].predict_score_matrix(home_team, away_team, max_goals)
    
    return {
        "home_team": home_team,
        "away_team": away_team,
        "matrix": matrix.tolist()
    }


@app.get("/likely-scores")
async def get_likely_scores(
    home_team: str,
    away_team: str,
    top_n: int = Query(default=5, le=15)
):
    """Get most likely exact scores"""
    if "poisson" not in models:
        raise HTTPException(status_code=500, detail="Poisson model not available")
    
    scores = models["poisson"].get_most_likely_scores(home_team, away_team, top_n)
    
    return {
        "home_team": home_team,
        "away_team": away_team,
        "scores": [{"score": s, "probability": p} for s, p in scores]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
