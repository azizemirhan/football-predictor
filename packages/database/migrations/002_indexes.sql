-- ============================================
-- Migration 002: Indexes
-- ============================================

-- Leagues
CREATE INDEX IF NOT EXISTS idx_leagues_country ON leagues(country);
CREATE INDEX IF NOT EXISTS idx_leagues_active ON leagues(is_active) WHERE is_active = true;

-- Seasons
CREATE INDEX IF NOT EXISTS idx_seasons_league ON seasons(league_id);
CREATE INDEX IF NOT EXISTS idx_seasons_current ON seasons(is_current) WHERE is_current = true;

-- Teams
CREATE INDEX IF NOT EXISTS idx_teams_name ON teams USING gin(name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_teams_country ON teams(country);

-- Team Seasons
CREATE INDEX IF NOT EXISTS idx_team_seasons_team ON team_seasons(team_id);
CREATE INDEX IF NOT EXISTS idx_team_seasons_season ON team_seasons(season_id);

-- Players
CREATE INDEX IF NOT EXISTS idx_players_team ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_players_name ON players USING gin(name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_players_position ON players(position);

-- Matches
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);
CREATE INDEX IF NOT EXISTS idx_matches_home_team ON matches(home_team_id);
CREATE INDEX IF NOT EXISTS idx_matches_away_team ON matches(away_team_id);
CREATE INDEX IF NOT EXISTS idx_matches_season ON matches(season_id);
CREATE INDEX IF NOT EXISTS idx_matches_upcoming ON matches(match_date, status) WHERE status = 'scheduled';

-- Match Stats
CREATE INDEX IF NOT EXISTS idx_match_stats_match ON match_stats(match_id);
CREATE INDEX IF NOT EXISTS idx_match_stats_team ON match_stats(team_id);

-- Team Ratings
CREATE INDEX IF NOT EXISTS idx_team_ratings_team ON team_ratings(team_id);
CREATE INDEX IF NOT EXISTS idx_team_ratings_type ON team_ratings(rating_type);

-- Predictions
CREATE INDEX IF NOT EXISTS idx_predictions_match ON predictions(match_id);
CREATE INDEX IF NOT EXISTS idx_predictions_model ON predictions(model_name);
CREATE INDEX IF NOT EXISTS idx_predictions_date ON predictions(created_at);

-- Odds
CREATE INDEX IF NOT EXISTS idx_odds_match ON odds(match_id);
CREATE INDEX IF NOT EXISTS idx_odds_bookmaker ON odds(bookmaker);
CREATE INDEX IF NOT EXISTS idx_odds_recorded ON odds(recorded_at);

-- Value Bets
CREATE INDEX IF NOT EXISTS idx_value_bets_match ON value_bets(match_id);
CREATE INDEX IF NOT EXISTS idx_value_bets_status ON value_bets(status);
CREATE INDEX IF NOT EXISTS idx_value_bets_edge ON value_bets(edge DESC);

-- News
CREATE INDEX IF NOT EXISTS idx_news_source ON news(source);
CREATE INDEX IF NOT EXISTS idx_news_published ON news(published_at);
CREATE INDEX IF NOT EXISTS idx_news_match ON news(match_id);

-- Scraping Logs
CREATE INDEX IF NOT EXISTS idx_scraping_logs_source ON scraping_logs(source);
CREATE INDEX IF NOT EXISTS idx_scraping_logs_status ON scraping_logs(status);
CREATE INDEX IF NOT EXISTS idx_scraping_logs_date ON scraping_logs(started_at);

-- Model Performance
CREATE INDEX IF NOT EXISTS idx_model_performance_model ON model_performance(model_name);
CREATE INDEX IF NOT EXISTS idx_model_performance_period ON model_performance(period_start, period_end);
