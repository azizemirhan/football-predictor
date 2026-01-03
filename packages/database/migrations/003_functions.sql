-- ============================================
-- Migration 003: Functions and Triggers
-- ============================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN 
        SELECT table_name 
        FROM information_schema.columns 
        WHERE column_name = 'updated_at' 
        AND table_schema = 'public'
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS update_%I_updated_at ON %I;
            CREATE TRIGGER update_%I_updated_at 
            BEFORE UPDATE ON %I
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        ', t, t, t, t);
    END LOOP;
END;
$$ language 'plpgsql';

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
    m.matchday,
    l.name as league_name,
    l.short_name as league_short,
    ht.id as home_team_id,
    ht.name as home_team,
    ht.short_name as home_team_short,
    ht.logo_url as home_team_logo,
    at.id as away_team_id,
    at.name as away_team,
    at.short_name as away_team_short,
    at.logo_url as away_team_logo,
    p.home_win_prob,
    p.draw_prob,
    p.away_win_prob,
    p.expected_home_goals,
    p.expected_away_goals,
    p.confidence,
    p.model_name
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

-- Team standings view
CREATE OR REPLACE VIEW team_standings_view AS
WITH match_results AS (
    SELECT 
        CASE WHEN home_score > away_score THEN home_team_id
             WHEN away_score > home_score THEN away_team_id
             ELSE NULL END as winner_id,
        CASE WHEN home_score = away_score THEN home_team_id ELSE NULL END as draw_home_id,
        CASE WHEN home_score = away_score THEN away_team_id ELSE NULL END as draw_away_id,
        home_team_id,
        away_team_id,
        home_score,
        away_score,
        season_id
    FROM matches
    WHERE status = 'finished'
)
SELECT 
    t.id as team_id,
    t.name as team_name,
    t.short_name,
    t.logo_url,
    s.id as season_id,
    s.name as season_name,
    COUNT(*) as played,
    SUM(CASE WHEN mr.winner_id = t.id THEN 1 ELSE 0 END) as won,
    SUM(CASE WHEN mr.draw_home_id = t.id OR mr.draw_away_id = t.id THEN 1 ELSE 0 END) as drawn,
    SUM(CASE WHEN mr.winner_id IS NOT NULL AND mr.winner_id != t.id THEN 1 ELSE 0 END) as lost,
    SUM(CASE WHEN mr.home_team_id = t.id THEN mr.home_score ELSE mr.away_score END) as goals_for,
    SUM(CASE WHEN mr.home_team_id = t.id THEN mr.away_score ELSE mr.home_score END) as goals_against,
    SUM(CASE WHEN mr.winner_id = t.id THEN 3 
             WHEN mr.draw_home_id = t.id OR mr.draw_away_id = t.id THEN 1 
             ELSE 0 END) as points
FROM teams t
JOIN team_seasons ts ON t.id = ts.team_id
JOIN seasons s ON ts.season_id = s.id
JOIN match_results mr ON (mr.home_team_id = t.id OR mr.away_team_id = t.id) AND mr.season_id = s.id
GROUP BY t.id, t.name, t.short_name, t.logo_url, s.id, s.name
ORDER BY points DESC, (goals_for - goals_against) DESC, goals_for DESC;

-- Value bets summary view
CREATE OR REPLACE VIEW value_bets_summary_view AS
SELECT 
    vb.*,
    m.match_date,
    m.status as match_status,
    ht.name as home_team,
    at.name as away_team,
    l.name as league_name
FROM value_bets vb
JOIN matches m ON vb.match_id = m.id
JOIN teams ht ON m.home_team_id = ht.id
JOIN teams at ON m.away_team_id = at.id
JOIN leagues l ON m.league_id = l.id
ORDER BY vb.edge DESC;
