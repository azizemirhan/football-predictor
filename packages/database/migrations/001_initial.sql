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
