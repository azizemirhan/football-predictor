-- ============================================================================
-- Football Predictor Pro - Supabase Database Schema
-- Run this in Supabase SQL Editor
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLES
-- ============================================================================

-- Leagues
CREATE TABLE IF NOT EXISTS leagues (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(50) NOT NULL,
    external_id VARCHAR(50) UNIQUE,
    logo_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Teams
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(20),
    league_id INTEGER REFERENCES leagues(id),
    logo_url TEXT,
    elo_rating DECIMAL(7,2) DEFAULT 1500.00,
    attack_strength DECIMAL(5,4) DEFAULT 1.0000,
    defense_strength DECIMAL(5,4) DEFAULT 1.0000,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Match status enum
CREATE TYPE match_status AS ENUM ('scheduled', 'live', 'finished', 'postponed', 'cancelled');

-- Matches
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    home_team_id INTEGER NOT NULL REFERENCES teams(id),
    away_team_id INTEGER NOT NULL REFERENCES teams(id),
    league_id INTEGER NOT NULL REFERENCES leagues(id),
    match_date TIMESTAMPTZ NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    status match_status DEFAULT 'scheduled',
    venue VARCHAR(100),
    external_id VARCHAR(100) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Predictions
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    model_name VARCHAR(50) NOT NULL,
    home_win_prob DECIMAL(5,4) NOT NULL,
    draw_prob DECIMAL(5,4) NOT NULL,
    away_win_prob DECIMAL(5,4) NOT NULL,
    confidence DECIMAL(5,4) DEFAULT 0.5,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Odds
CREATE TABLE IF NOT EXISTS odds (
    id SERIAL PRIMARY KEY,
    match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    bookmaker VARCHAR(50) NOT NULL,
    market_type VARCHAR(20) NOT NULL DEFAULT '1X2',
    home_odds DECIMAL(6,2),
    draw_odds DECIMAL(6,2),
    away_odds DECIMAL(6,2),
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bet result enum
CREATE TYPE bet_result AS ENUM ('pending', 'won', 'lost', 'void');

-- Value Bets
CREATE TABLE IF NOT EXISTS value_bets (
    id SERIAL PRIMARY KEY,
    match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    prediction_id INTEGER NOT NULL REFERENCES predictions(id) ON DELETE CASCADE,
    selection VARCHAR(20) NOT NULL,
    predicted_prob DECIMAL(5,4) NOT NULL,
    market_odds DECIMAL(6,2) NOT NULL,
    edge DECIMAL(5,4) NOT NULL,
    kelly_stake DECIMAL(5,4) DEFAULT 0,
    result bet_result DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);
CREATE INDEX IF NOT EXISTS idx_matches_league ON matches(league_id);
CREATE INDEX IF NOT EXISTS idx_predictions_match ON predictions(match_id);
CREATE INDEX IF NOT EXISTS idx_odds_match ON odds(match_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_value_bets_result ON value_bets(result);
CREATE INDEX IF NOT EXISTS idx_teams_league ON teams(league_id);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE leagues ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE odds ENABLE ROW LEVEL SECURITY;
ALTER TABLE value_bets ENABLE ROW LEVEL SECURITY;

-- Allow public read access
CREATE POLICY "Allow public read" ON leagues FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON teams FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON matches FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON predictions FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON odds FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON value_bets FOR SELECT USING (true);

-- Allow service role to insert/update/delete
CREATE POLICY "Allow service role insert" ON leagues FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow service role update" ON leagues FOR UPDATE USING (true);

CREATE POLICY "Allow service role insert" ON teams FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow service role update" ON teams FOR UPDATE USING (true);

CREATE POLICY "Allow service role insert" ON matches FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow service role update" ON matches FOR UPDATE USING (true);

CREATE POLICY "Allow service role insert" ON predictions FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow service role update" ON predictions FOR UPDATE USING (true);

CREATE POLICY "Allow service role insert" ON odds FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow service role update" ON odds FOR UPDATE USING (true);

CREATE POLICY "Allow service role insert" ON value_bets FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow service role update" ON value_bets FOR UPDATE USING (true);

-- ============================================================================
-- SEED DATA - Premier League
-- ============================================================================

-- Insert Premier League
INSERT INTO leagues (name, country, external_id) VALUES 
('Premier League', 'England', 'PL')
ON CONFLICT (external_id) DO NOTHING;

-- Insert Premier League Teams (2024-25 Season)
INSERT INTO teams (name, short_name, league_id, elo_rating) VALUES 
('Arsenal', 'ARS', 1, 1850),
('Aston Villa', 'AVL', 1, 1720),
('Bournemouth', 'BOU', 1, 1580),
('Brentford', 'BRE', 1, 1620),
('Brighton', 'BHA', 1, 1680),
('Chelsea', 'CHE', 1, 1780),
('Crystal Palace', 'CRY', 1, 1600),
('Everton', 'EVE', 1, 1560),
('Fulham', 'FUL', 1, 1620),
('Ipswich Town', 'IPS', 1, 1500),
('Leicester City', 'LEI', 1, 1540),
('Liverpool', 'LIV', 1, 1880),
('Manchester City', 'MCI', 1, 1920),
('Manchester United', 'MUN', 1, 1750),
('Newcastle United', 'NEW', 1, 1740),
('Nottingham Forest', 'NFO', 1, 1580),
('Southampton', 'SOU', 1, 1480),
('Tottenham', 'TOT', 1, 1760),
('West Ham', 'WHU', 1, 1660),
('Wolves', 'WOL', 1, 1600)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to tables
CREATE TRIGGER update_leagues_updated_at
    BEFORE UPDATE ON leagues
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_teams_updated_at
    BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_matches_updated_at
    BEFORE UPDATE ON matches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
