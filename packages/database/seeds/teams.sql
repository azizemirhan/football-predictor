-- ============================================
-- Seed: Premier League Teams 2024-25
-- ============================================

INSERT INTO teams (name, short_name, code, stadium, city, country, founded_year) VALUES
('Arsenal', 'Arsenal', 'ARS', 'Emirates Stadium', 'London', 'England', 1886),
('Aston Villa', 'Aston Villa', 'AVL', 'Villa Park', 'Birmingham', 'England', 1874),
('Bournemouth', 'Bournemouth', 'BOU', 'Vitality Stadium', 'Bournemouth', 'England', 1899),
('Brentford', 'Brentford', 'BRE', 'Gtech Community Stadium', 'London', 'England', 1889),
('Brighton', 'Brighton', 'BHA', 'American Express Stadium', 'Brighton', 'England', 1901),
('Chelsea', 'Chelsea', 'CHE', 'Stamford Bridge', 'London', 'England', 1905),
('Crystal Palace', 'Crystal P', 'CRY', 'Selhurst Park', 'London', 'England', 1905),
('Everton', 'Everton', 'EVE', 'Goodison Park', 'Liverpool', 'England', 1878),
('Fulham', 'Fulham', 'FUL', 'Craven Cottage', 'London', 'England', 1879),
('Ipswich Town', 'Ipswich', 'IPS', 'Portman Road', 'Ipswich', 'England', 1878),
('Leicester City', 'Leicester', 'LEI', 'King Power Stadium', 'Leicester', 'England', 1884),
('Liverpool', 'Liverpool', 'LIV', 'Anfield', 'Liverpool', 'England', 1892),
('Manchester City', 'Man City', 'MCI', 'Etihad Stadium', 'Manchester', 'England', 1880),
('Manchester United', 'Man Utd', 'MUN', 'Old Trafford', 'Manchester', 'England', 1878),
('Newcastle United', 'Newcastle', 'NEW', 'St James'' Park', 'Newcastle', 'England', 1892),
('Nottingham Forest', 'Nott''m Forest', 'NFO', 'City Ground', 'Nottingham', 'England', 1865),
('Southampton', 'Southampton', 'SOU', 'St Mary''s Stadium', 'Southampton', 'England', 1885),
('Tottenham Hotspur', 'Spurs', 'TOT', 'Tottenham Hotspur Stadium', 'London', 'England', 1882),
('West Ham United', 'West Ham', 'WHU', 'London Stadium', 'London', 'England', 1895),
('Wolverhampton', 'Wolves', 'WOL', 'Molineux Stadium', 'Wolverhampton', 'England', 1877)
ON CONFLICT DO NOTHING;

-- Link teams to current season
INSERT INTO team_seasons (team_id, season_id, league_id)
SELECT t.id, s.id, l.id
FROM teams t
CROSS JOIN seasons s
JOIN leagues l ON s.league_id = l.id
WHERE t.country = 'England' 
AND l.short_name = 'EPL'
AND s.is_current = true
ON CONFLICT DO NOTHING;

-- Initialize Elo ratings for all teams
INSERT INTO team_ratings (team_id, rating_type, rating, matches_played)
SELECT id, 'elo', 
    CASE 
        WHEN name IN ('Manchester City', 'Liverpool', 'Arsenal') THEN 1850
        WHEN name IN ('Chelsea', 'Tottenham Hotspur', 'Manchester United', 'Newcastle United') THEN 1750
        WHEN name IN ('Aston Villa', 'Brighton', 'West Ham United') THEN 1650
        ELSE 1500
    END,
    0
FROM teams
WHERE country = 'England'
ON CONFLICT DO NOTHING;
