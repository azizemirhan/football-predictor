-- ============================================
-- Migration 001: Initial Schema
-- Football Predictor Pro
-- ============================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Leagues
CREATE TABLE IF NOT EXISTS leagues (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(20),
    country VARCHAR(50) NOT NULL,
    country_code CHAR(2),
    logo_url TEXT,
    external_id VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seasons
CREATE TABLE IF NOT EXISTS seasons (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    league_id INTEGER REFERENCES leagues(id) ON DELETE CASCADE,
    name VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(league_id, name)
);

-- Teams
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(20),
    code VARCHAR(5),
    logo_url TEXT,
    stadium VARCHAR(100),
    stadium_capacity INTEGER,
    city VARCHAR(50),
    country VARCHAR(50),
    founded_year INTEGER,
    external_ids JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Team Seasons
CREATE TABLE IF NOT EXISTS team_seasons (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    season_id INTEGER REFERENCES seasons(id) ON DELETE CASCADE,
    league_id INTEGER REFERENCES leagues(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(team_id, season_id)
);

-- Players
CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(50),
    nationality VARCHAR(50),
    birth_date DATE,
    height_cm INTEGER,
    weight_kg INTEGER,
    position VARCHAR(20),
    jersey_number INTEGER,
    photo_url TEXT,
    market_value DECIMAL(15,2),
    market_value_currency VARCHAR(3) DEFAULT 'EUR',
    external_ids JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Matches
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    season_id INTEGER REFERENCES seasons(id) ON DELETE CASCADE,
    league_id INTEGER REFERENCES leagues(id) ON DELETE CASCADE,
    home_team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    away_team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    match_date TIMESTAMPTZ NOT NULL,
    matchday INTEGER,
    venue VARCHAR(100),
    referee VARCHAR(100),
    status VARCHAR(20) DEFAULT 'scheduled',
    minute INTEGER,
    home_score INTEGER,
    away_score INTEGER,
    home_score_ht INTEGER,
    away_score_ht INTEGER,
    external_ids JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Match Stats
CREATE TABLE IF NOT EXISTS match_stats (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    possession DECIMAL(5,2),
    shots INTEGER DEFAULT 0,
    shots_on_target INTEGER DEFAULT 0,
    corners INTEGER DEFAULT 0,
    fouls INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    passes INTEGER DEFAULT 0,
    pass_accuracy DECIMAL(5,2),
    xg DECIMAL(5,3),
    xg_against DECIMAL(5,3),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(match_id, team_id)
);

-- Team Ratings
CREATE TABLE IF NOT EXISTS team_ratings (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    rating_type VARCHAR(20) NOT NULL,
    rating DECIMAL(10,4) NOT NULL,
    rating_deviation DECIMAL(10,4),
    volatility DECIMAL(10,6),
    matches_played INTEGER DEFAULT 0,
    last_match_id INTEGER REFERENCES matches(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(team_id, rating_type)
);

-- Predictions
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    model_name VARCHAR(50) NOT NULL,
    model_version VARCHAR(20),
    home_win_prob DECIMAL(5,4) NOT NULL,
    draw_prob DECIMAL(5,4) NOT NULL,
    away_win_prob DECIMAL(5,4) NOT NULL,
    expected_home_goals DECIMAL(5,3),
    expected_away_goals DECIMAL(5,3),
    most_likely_score VARCHAR(10),
    confidence DECIMAL(5,4),
    reasoning TEXT,
    factors JSONB,
    is_correct BOOLEAN,
    actual_result CHAR(1),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Odds
CREATE TABLE IF NOT EXISTS odds (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    bookmaker VARCHAR(50) NOT NULL,
    market_type VARCHAR(30) NOT NULL,
    home_odds DECIMAL(8,3),
    draw_odds DECIMAL(8,3),
    away_odds DECIMAL(8,3),
    over_under JSONB,
    btts_yes DECIMAL(8,3),
    btts_no DECIMAL(8,3),
    is_opening BOOLEAN DEFAULT false,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Value Bets
CREATE TABLE IF NOT EXISTS value_bets (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    prediction_id INTEGER REFERENCES predictions(id) ON DELETE CASCADE,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    selection VARCHAR(20) NOT NULL,
    market_type VARCHAR(30) NOT NULL,
    bookmaker VARCHAR(50),
    odds DECIMAL(8,3) NOT NULL,
    predicted_prob DECIMAL(5,4) NOT NULL,
    implied_prob DECIMAL(5,4) NOT NULL,
    edge DECIMAL(5,4) NOT NULL,
    kelly_fraction DECIMAL(6,4),
    recommended_stake DECIMAL(5,4),
    status VARCHAR(20) DEFAULT 'pending',
    profit_loss DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- News
CREATE TABLE IF NOT EXISTS news (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    source VARCHAR(50) NOT NULL,
    source_url TEXT,
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    sentiment_score DECIMAL(4,3),
    importance_score DECIMAL(4,3),
    categories JSONB,
    teams JSONB,
    players JSONB,
    match_id INTEGER REFERENCES matches(id),
    published_at TIMESTAMPTZ,
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(100),
    avatar_url TEXT,
    preferences JSONB DEFAULT '{}',
    subscription_tier VARCHAR(20) DEFAULT 'free',
    subscription_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scraping Logs
CREATE TABLE IF NOT EXISTS scraping_logs (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    records_processed INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER
);

-- Model Performance
CREATE TABLE IF NOT EXISTS model_performance (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(50) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    period_type VARCHAR(10) NOT NULL,
    predictions_count INTEGER DEFAULT 0,
    correct_predictions INTEGER DEFAULT 0,
    accuracy DECIMAL(5,4),
    log_loss DECIMAL(6,4),
    brier_score DECIMAL(6,4),
    rps DECIMAL(6,4),
    roi DECIMAL(8,4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(model_name, period_start, period_end, period_type)
);
