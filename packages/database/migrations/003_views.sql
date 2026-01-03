-- ============================================================================
-- Views
-- ============================================================================

-- Upcoming matches with team details
CREATE OR REPLACE VIEW v_upcoming_matches AS
SELECT 
    m.id,
    m.match_date,
    m.league,
    m.season,
    m.venue,
    ht.name as home_team,
    ht.short_name as home_short,
    at.name as away_team,
    at.short_name as away_short,
    m.status
FROM matches m
JOIN teams ht ON m.home_team_id = ht.id
JOIN teams at ON m.away_team_id = at.id
WHERE m.status = 'scheduled'
ORDER BY m.match_date;

-- Match results with predictions
CREATE OR REPLACE VIEW v_match_predictions AS
SELECT 
    m.id as match_id,
    m.match_date,
    ht.name as home_team,
    at.name as away_team,
    m.home_score,
    m.away_score,
    p.model_name,
    p.home_win_prob,
    p.draw_prob,
    p.away_win_prob,
    p.confidence,
    CASE 
        WHEN m.home_score > m.away_score THEN 'H'
        WHEN m.home_score < m.away_score THEN 'A'
        ELSE 'D'
    END as actual_result,
    CASE 
        WHEN p.home_win_prob > p.draw_prob AND p.home_win_prob > p.away_win_prob THEN 'H'
        WHEN p.away_win_prob > p.draw_prob AND p.away_win_prob > p.home_win_prob THEN 'A'
        ELSE 'D'
    END as predicted_result
FROM matches m
JOIN teams ht ON m.home_team_id = ht.id
JOIN teams at ON m.away_team_id = at.id
LEFT JOIN predictions p ON m.id = p.match_id
WHERE m.status = 'finished';

-- Team form (last 5 matches)
CREATE OR REPLACE VIEW v_team_form AS
WITH recent_matches AS (
    SELECT 
        t.id as team_id,
        t.name as team_name,
        m.id as match_id,
        m.match_date,
        CASE WHEN m.home_team_id = t.id THEN m.home_score ELSE m.away_score END as goals_for,
        CASE WHEN m.home_team_id = t.id THEN m.away_score ELSE m.home_score END as goals_against,
        ROW_NUMBER() OVER (PARTITION BY t.id ORDER BY m.match_date DESC) as rn
    FROM teams t
    JOIN matches m ON t.id IN (m.home_team_id, m.away_team_id)
    WHERE m.status = 'finished'
)
SELECT 
    team_id,
    team_name,
    COUNT(*) as matches,
    SUM(CASE WHEN goals_for > goals_against THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN goals_for = goals_against THEN 1 ELSE 0 END) as draws,
    SUM(CASE WHEN goals_for < goals_against THEN 1 ELSE 0 END) as losses,
    SUM(goals_for) as goals_for,
    SUM(goals_against) as goals_against,
    SUM(CASE WHEN goals_for > goals_against THEN 3 WHEN goals_for = goals_against THEN 1 ELSE 0 END) as points
FROM recent_matches
WHERE rn <= 5
GROUP BY team_id, team_name;
