-- ============================================
-- Seed: Leagues
-- ============================================

INSERT INTO leagues (name, short_name, country, country_code, priority, is_active) VALUES
('Premier League', 'EPL', 'England', 'GB', 1, true),
('La Liga', 'LAL', 'Spain', 'ES', 2, true),
('Bundesliga', 'BUN', 'Germany', 'DE', 3, true),
('Serie A', 'SEA', 'Italy', 'IT', 4, true),
('Ligue 1', 'L1', 'France', 'FR', 5, true),
('Eredivisie', 'ERE', 'Netherlands', 'NL', 6, true),
('Primeira Liga', 'PRI', 'Portugal', 'PT', 7, true),
('Super Lig', 'SUP', 'Turkey', 'TR', 8, true),
('Scottish Premiership', 'SPL', 'Scotland', 'GB', 9, true),
('Championship', 'ELC', 'England', 'GB', 10, true)
ON CONFLICT DO NOTHING;

-- Current season
INSERT INTO seasons (league_id, name, start_date, end_date, is_current)
SELECT id, '2024-25', '2024-08-01', '2025-05-31', true
FROM leagues WHERE short_name = 'EPL'
ON CONFLICT DO NOTHING;
