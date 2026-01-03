-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Teams
CREATE INDEX idx_teams_country ON teams(country);
CREATE INDEX idx_teams_league ON teams(league);
CREATE INDEX idx_teams_name_trgm ON teams USING gin (name gin_trgm_ops);

-- Players
CREATE INDEX idx_players_team ON players(team_id);
CREATE INDEX idx_players_name_trgm ON players USING gin (name gin_trgm_ops);

-- Matches
CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_matches_league_season ON matches(league, season);
CREATE INDEX idx_matches_home_team ON matches(home_team_id);
CREATE INDEX idx_matches_away_team ON matches(away_team_id);
CREATE INDEX idx_matches_status ON matches(status);

-- Match Stats
CREATE INDEX idx_match_stats_match ON match_stats(match_id);

-- News
CREATE INDEX idx_news_published ON news(published_at DESC);
CREATE INDEX idx_news_source ON news(source);
CREATE INDEX idx_news_sentiment ON news(sentiment_score);
CREATE INDEX idx_news_title_trgm ON news USING gin (title gin_trgm_ops);

-- Odds
CREATE INDEX idx_odds_match ON odds(match_id);
CREATE INDEX idx_odds_bookmaker ON odds(bookmaker);
CREATE INDEX idx_odds_recorded ON odds(recorded_at);

-- Predictions
CREATE INDEX idx_predictions_match ON predictions(match_id);
CREATE INDEX idx_predictions_model ON predictions(model_name);
CREATE INDEX idx_predictions_created ON predictions(created_at DESC);

-- Value Bets
CREATE INDEX idx_value_bets_match ON value_bets(match_id);
CREATE INDEX idx_value_bets_edge ON value_bets(edge DESC);
CREATE INDEX idx_value_bets_result ON value_bets(result);

-- Elo Ratings
CREATE INDEX idx_elo_team_date ON elo_ratings(team_id, rating_date DESC);
