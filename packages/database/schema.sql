-- ============================================
-- Football Predictor Pro - Database Schema
-- Version: 1.0.0
-- ============================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================
-- LEAGUES TABLE
-- ============================================
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

CREATE INDEX idx_leagues_country ON leagues(country);
CREATE INDEX idx_leagues_active ON leagues(is_active) WHERE is_active = true;

-- ============================================
-- SEASONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS seasons (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    league_id INTEGER REFERENCES leagues(id) ON DELETE CASCADE,
    name VARCHAR(20) NOT NULL, -- e.g., "2024-25"
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(league_id, name)
);

CREATE INDEX idx_seasons_league ON seasons(league_id);
CREATE INDEX idx_seasons_current ON seasons(is_current) WHERE is_current = true;

-- ============================================
-- TEAMS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(10),
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

CREATE INDEX idx_teams_name ON teams USING gin(name gin_trgm_ops);
CREATE INDEX idx_teams_country ON teams(country);

-- ============================================
-- TEAM_SEASONS (Many-to-Many)
-- ============================================
CREATE TABLE IF NOT EXISTS team_seasons (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    season_id INTEGER REFERENCES seasons(id) ON DELETE CASCADE,
    league_id INTEGER REFERENCES leagues(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(team_id, season_id)
);

CREATE INDEX idx_team_seasons_team ON team_seasons(team_id);
CREATE INDEX idx_team_seasons_season ON team_seasons(season_id);

-- ============================================
-- PLAYERS TABLE
-- ============================================
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
    position VARCHAR(20), -- GK, DEF, MID, FWD
    jersey_number INTEGER,
    photo_url TEXT,
    market_value DECIMAL(15,2),
    market_value_currency VARCHAR(3) DEFAULT 'EUR',
    external_ids JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_players_team ON players(team_id);
CREATE INDEX idx_players_name ON players USING gin(name gin_trgm_ops);
CREATE INDEX idx_players_position ON players(position);

-- ============================================
-- MATCHES TABLE
-- ============================================
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
    
    -- Status
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, live, finished, postponed, cancelled
    minute INTEGER,
    
    -- Scores
    home_score INTEGER,
    away_score INTEGER,
    home_score_ht INTEGER,
    away_score_ht INTEGER,
    
    -- External references
    external_ids JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_matches_status ON matches(status);
CREATE INDEX idx_matches_home_team ON matches(home_team_id);
CREATE INDEX idx_matches_away_team ON matches(away_team_id);
CREATE INDEX idx_matches_season ON matches(season_id);
CREATE INDEX idx_matches_upcoming ON matches(match_date, status) 
    WHERE status = 'scheduled';

-- ============================================
-- MATCH_STATS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS match_stats (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    
    -- Basic stats
    possession DECIMAL(5,2),
    shots INTEGER DEFAULT 0,
    shots_on_target INTEGER DEFAULT 0,
    shots_off_target INTEGER DEFAULT 0,
    blocked_shots INTEGER DEFAULT 0,
    corners INTEGER DEFAULT 0,
    offsides INTEGER DEFAULT 0,
    fouls INTEGER DEFAULT 0,
    
    -- Cards
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    
    -- Passes
    passes INTEGER DEFAULT 0,
    pass_accuracy DECIMAL(5,2),
    key_passes INTEGER DEFAULT 0,
    crosses INTEGER DEFAULT 0,
    
    -- Defense
    tackles INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    clearances INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    
    -- xG metrics
    xg DECIMAL(5,3),
    xg_against DECIMAL(5,3),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(match_id, team_id)
);

CREATE INDEX idx_match_stats_match ON match_stats(match_id);
CREATE INDEX idx_match_stats_team ON match_stats(team_id);

-- ============================================
-- TEAM_RATINGS TABLE (Elo, etc.)
-- ============================================
CREATE TABLE IF NOT EXISTS team_ratings (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    rating_type VARCHAR(20) NOT NULL, -- elo, glicko, etc.
    rating DECIMAL(10,4) NOT NULL,
    rating_deviation DECIMAL(10,4), -- for Glicko
    volatility DECIMAL(10,6), -- for Glicko-2
    matches_played INTEGER DEFAULT 0,
    last_match_id INTEGER REFERENCES matches(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(team_id, rating_type)
);

CREATE INDEX idx_team_ratings_team ON team_ratings(team_id);
CREATE INDEX idx_team_ratings_type ON team_ratings(rating_type);

-- ============================================
-- PREDICTIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    
    -- Model info
    model_name VARCHAR(50) NOT NULL, -- ensemble, poisson, elo, xgboost, llm, etc.
    model_version VARCHAR(20),
    
    -- Probabilities
    home_win_prob DECIMAL(5,4) NOT NULL,
    draw_prob DECIMAL(5,4) NOT NULL,
    away_win_prob DECIMAL(5,4) NOT NULL,
    
    -- Score predictions
    expected_home_goals DECIMAL(5,3),
    expected_away_goals DECIMAL(5,3),
    most_likely_score VARCHAR(10),
    
    -- Confidence
    confidence DECIMAL(5,4),
    
    -- Analysis
    reasoning TEXT,
    factors JSONB, -- {"form": 0.8, "h2h": 0.6, ...}
    
    -- Result tracking
    is_correct BOOLEAN,
    actual_result CHAR(1), -- H, D, A
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_predictions_match ON predictions(match_id);
CREATE INDEX idx_predictions_model ON predictions(model_name);
CREATE INDEX idx_predictions_date ON predictions(created_at);

-- ============================================
-- ODDS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS odds (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    bookmaker VARCHAR(50) NOT NULL,
    market_type VARCHAR(30) NOT NULL, -- 1x2, over_under, btts, etc.
    
    -- 1X2 odds
    home_odds DECIMAL(8,3),
    draw_odds DECIMAL(8,3),
    away_odds DECIMAL(8,3),
    
    -- Over/Under (stored as JSONB for flexibility)
    over_under JSONB, -- {"0.5": {"over": 1.1, "under": 8.0}, "2.5": {...}}
    
    -- BTTS
    btts_yes DECIMAL(8,3),
    btts_no DECIMAL(8,3),
    
    -- Metadata
    is_opening BOOLEAN DEFAULT false,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_odds_match ON odds(match_id);
CREATE INDEX idx_odds_bookmaker ON odds(bookmaker);
CREATE INDEX idx_odds_recorded ON odds(recorded_at);

-- ============================================
-- VALUE_BETS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS value_bets (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    prediction_id INTEGER REFERENCES predictions(id) ON DELETE CASCADE,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    
    -- Bet details
    selection VARCHAR(20) NOT NULL, -- home_win, draw, away_win, over_2.5, etc.
    market_type VARCHAR(30) NOT NULL,
    bookmaker VARCHAR(50),
    
    -- Values
    odds DECIMAL(8,3) NOT NULL,
    predicted_prob DECIMAL(5,4) NOT NULL,
    implied_prob DECIMAL(5,4) NOT NULL,
    edge DECIMAL(5,4) NOT NULL,
    
    -- Kelly
    kelly_fraction DECIMAL(6,4),
    recommended_stake DECIMAL(5,4),
    
    -- Result tracking
    status VARCHAR(20) DEFAULT 'pending', -- pending, won, lost, void
    profit_loss DECIMAL(10,2),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX idx_value_bets_match ON value_bets(match_id);
CREATE INDEX idx_value_bets_status ON value_bets(status);
CREATE INDEX idx_value_bets_edge ON value_bets(edge DESC);

-- ============================================
-- NEWS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS news (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    
    -- Source
    source VARCHAR(50) NOT NULL, -- bbc, sky_sports, guardian, etc.
    source_url TEXT,
    
    -- Content
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    
    -- Analysis
    sentiment_score DECIMAL(4,3), -- -1 to 1
    importance_score DECIMAL(4,3), -- 0 to 1
    categories JSONB, -- ["injury", "transfer", "match_preview"]
    
    -- Relations
    teams JSONB, -- [team_id, team_id, ...]
    players JSONB, -- [player_id, ...]
    match_id INTEGER REFERENCES matches(id),
    
    published_at TIMESTAMPTZ,
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX idx_news_source ON news(source);
CREATE INDEX idx_news_published ON news(published_at);
CREATE INDEX idx_news_match ON news(match_id);
CREATE INDEX idx_news_search ON news USING gin(to_tsvector('english', title || ' ' || COALESCE(content, '')));

-- ============================================
-- USERS TABLE (Supabase auth integration)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY, -- Links to Supabase auth.users
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(100),
    avatar_url TEXT,
    
    -- Preferences
    preferences JSONB DEFAULT '{}',
    
    -- Subscription
    subscription_tier VARCHAR(20) DEFAULT 'free', -- free, pro, enterprise
    subscription_expires_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- USER_ALERTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS user_alerts (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    alert_type VARCHAR(30) NOT NULL, -- value_bet, match_start, goal, etc.
    team_id INTEGER REFERENCES teams(id),
    match_id INTEGER REFERENCES matches(id),
    
    -- Conditions
    conditions JSONB, -- {"min_edge": 0.05, "max_odds": 3.0}
    
    -- Notification
    notify_email BOOLEAN DEFAULT false,
    notify_telegram BOOLEAN DEFAULT false,
    notify_discord BOOLEAN DEFAULT false,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_alerts_user ON user_alerts(user_id);
CREATE INDEX idx_user_alerts_active ON user_alerts(is_active) WHERE is_active = true;

-- ============================================
-- BETTING_HISTORY TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS betting_history (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    value_bet_id INTEGER REFERENCES value_bets(id),
    match_id INTEGER REFERENCES matches(id),
    
    -- Bet details
    selection VARCHAR(30) NOT NULL,
    odds DECIMAL(8,3) NOT NULL,
    stake DECIMAL(10,2) NOT NULL,
    potential_return DECIMAL(12,2),
    
    -- Result
    status VARCHAR(20) DEFAULT 'pending', -- pending, won, lost, void
    profit_loss DECIMAL(10,2),
    
    placed_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX idx_betting_history_user ON betting_history(user_id);
CREATE INDEX idx_betting_history_status ON betting_history(status);

-- ============================================
-- MODEL_PERFORMANCE TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS model_performance (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(50) NOT NULL,
    
    -- Time period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    period_type VARCHAR(10) NOT NULL, -- daily, weekly, monthly
    
    -- Metrics
    predictions_count INTEGER DEFAULT 0,
    correct_predictions INTEGER DEFAULT 0,
    accuracy DECIMAL(5,4),
    log_loss DECIMAL(6,4),
    brier_score DECIMAL(6,4),
    rps DECIMAL(6,4), -- Ranked Probability Score
    roi DECIMAL(8,4),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(model_name, period_start, period_end, period_type)
);

CREATE INDEX idx_model_performance_model ON model_performance(model_name);
CREATE INDEX idx_model_performance_period ON model_performance(period_start, period_end);

-- ============================================
-- SCRAPING_LOGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS scraping_logs (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    task_type VARCHAR(50) NOT NULL, -- matches, odds, news, stats
    
    status VARCHAR(20) NOT NULL, -- started, completed, failed
    records_processed INTEGER DEFAULT 0,
    error_message TEXT,
    
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER
);

CREATE INDEX idx_scraping_logs_source ON scraping_logs(source);
CREATE INDEX idx_scraping_logs_status ON scraping_logs(status);
CREATE INDEX idx_scraping_logs_date ON scraping_logs(started_at);

-- ============================================
-- UPDATE TIMESTAMP TRIGGER
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all tables with updated_at
CREATE TRIGGER update_leagues_updated_at BEFORE UPDATE ON leagues
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_seasons_updated_at BEFORE UPDATE ON seasons
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_players_updated_at BEFORE UPDATE ON players
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_matches_updated_at BEFORE UPDATE ON matches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_match_stats_updated_at BEFORE UPDATE ON match_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_team_ratings_updated_at BEFORE UPDATE ON team_ratings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- VIEWS
-- ============================================

-- Upcoming matches with predictions
CREATE OR REPLACE VIEW upcoming_matches_view AS
SELECT 
    m.id,
    m.uuid,
    m.match_date,
    m.status,
    l.name as league_name,
    ht.name as home_team,
    ht.short_name as home_team_short,
    at.name as away_team,
    at.short_name as away_team_short,
    p.home_win_prob,
    p.draw_prob,
    p.away_win_prob,
    p.confidence
FROM matches m
JOIN leagues l ON m.league_id = l.id
JOIN teams ht ON m.home_team_id = ht.id
JOIN teams at ON m.away_team_id = at.id
LEFT JOIN LATERAL (
    SELECT * FROM predictions 
    WHERE match_id = m.id AND model_name = 'ensemble'
    ORDER BY created_at DESC LIMIT 1
) p ON true
WHERE m.status = 'scheduled' AND m.match_date > NOW()
ORDER BY m.match_date;

-- Team form view (last 5 matches)
CREATE OR REPLACE VIEW team_form_view AS
WITH recent_matches AS (
    SELECT 
        t.id as team_id,
        t.name as team_name,
        m.id as match_id,
        m.match_date,
        CASE 
            WHEN m.home_team_id = t.id AND m.home_score > m.away_score THEN 'W'
            WHEN m.away_team_id = t.id AND m.away_score > m.home_score THEN 'W'
            WHEN m.home_score = m.away_score THEN 'D'
            ELSE 'L'
        END as result,
        ROW_NUMBER() OVER (PARTITION BY t.id ORDER BY m.match_date DESC) as rn
    FROM teams t
    LEFT JOIN matches m ON (m.home_team_id = t.id OR m.away_team_id = t.id)
    WHERE m.status = 'finished'
)
SELECT 
    team_id,
    team_name,
    STRING_AGG(result, '' ORDER BY rn) as form,
    SUM(CASE WHEN result = 'W' THEN 3 WHEN result = 'D' THEN 1 ELSE 0 END) as points
FROM recent_matches
WHERE rn <= 5
GROUP BY team_id, team_name;

-- ============================================
-- INITIAL DATA
-- ============================================

-- Premier League
INSERT INTO leagues (name, short_name, country, country_code, priority, is_active)
VALUES ('Premier League', 'EPL', 'England', 'GB', 1, true)
ON CONFLICT DO NOTHING;
