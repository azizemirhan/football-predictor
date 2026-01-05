const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');
const { distance } = require('fastest-levenshtein');

// Load env
const envPath = path.resolve(__dirname, '.env.local');
const envContent = fs.readFileSync(envPath, 'utf8');
envContent.split('\n').forEach(line => {
    const idx = line.indexOf('=');
    if (idx > 0) process.env[line.substring(0, idx).trim()] = line.substring(idx + 1).trim();
});

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

function normalizeName(name) {
    if (!name) return '';
    return name.toLowerCase()
        .replace(/ü/g, 'u').replace(/ğ/g, 'g').replace(/ı/g, 'i')
        .replace(/ş/g, 's').replace(/ç/g, 'c').replace(/ö/g, 'o')
        .replace(/[^a-z0-9 ]/g, '').trim();
}

function buildAliasMap(aliases) {
    const map = new Map();
    for (const a of aliases) {
        map.set(normalizeName(a.alias), a.team_id);
    }
    return map;
}

function findMatchingMatch(scrapedMatch, dbMatches, aliasMap) {
    const scrapedHome = scrapedMatch.homeTeam;
    const scrapedAway = scrapedMatch.awayTeam;
    const scrapedDate = scrapedMatch.date;

    // 1. Filter by date
    const sameDateMatches = dbMatches.filter(m => {
        const dbDate = new Date(m.match_date);
        const day = String(dbDate.getDate()).padStart(2, '0');
        const month = String(dbDate.getMonth() + 1).padStart(2, '0');
        const year = dbDate.getFullYear();
        const formattedDbDate = `${day}.${month}.${year}`;
        return formattedDbDate === scrapedDate;
    });

    if (sameDateMatches.length === 0) return null;

    // 2. Try alias match
    if (aliasMap) {
        const homeTeamId = aliasMap.get(normalizeName(scrapedHome));
        const awayTeamId = aliasMap.get(normalizeName(scrapedAway));

        if (homeTeamId && awayTeamId) {
            const exactMatch = sameDateMatches.find(m => 
                m.home_team?.id === homeTeamId && m.away_team?.id === awayTeamId
            );
            if (exactMatch) return exactMatch;
        }
    }

    // 3. Fuzzy fallback
    let bestMatch = null;
    let minDistance = Infinity;
    const normalizedHome = normalizeName(scrapedHome);
    const normalizedAway = normalizeName(scrapedAway);

    for (const dbMatch of sameDateMatches) {
        if (!dbMatch.home_team || !dbMatch.away_team) continue;
        const dbHome = normalizeName(dbMatch.home_team.name);
        const dbAway = normalizeName(dbMatch.away_team.name);
        const distHome = distance(normalizedHome, dbHome);
        const distAway = distance(normalizedAway, dbAway);
        const totalDist = distHome + distAway;
        if (totalDist < 12 && totalDist < minDistance) {
            minDistance = totalDist;
            bestMatch = dbMatch;
        }
    }

    return bestMatch;
}

async function simulate() {
    // Get DB matches EXACTLY as the API does
    const today = new Date();
    const past = new Date(today); past.setDate(today.getDate() - 1);
    const future = new Date(today); future.setDate(today.getDate() + 14);

    const { data: rawDbMatches } = await supabase
        .from('matches')
        .select(`
            id, match_date, status,
            home_team:teams!matches_home_team_id_fkey(id, name, elo_rating),
            away_team:teams!matches_away_team_id_fkey(id, name, elo_rating)
        `)
        .gte('match_date', past.toISOString())
        .lte('match_date', future.toISOString());

    // Check structure
    const sample = rawDbMatches?.[0];
    console.log('Sample DB match structure:');
    console.log('  home_team:', typeof sample?.home_team, Array.isArray(sample?.home_team) ? 'ARRAY!' : 'object');
    console.log('  home_team.id:', sample?.home_team?.id);
    
    // Normalize if needed
    const dbMatches = rawDbMatches?.map(m => ({
        ...m,
        home_team: Array.isArray(m.home_team) ? m.home_team[0] : m.home_team,
        away_team: Array.isArray(m.away_team) ? m.away_team[0] : m.away_team
    })) || [];

    console.log('\nDB Matches count:', dbMatches.length);

    // Get aliases
    const { data: aliases } = await supabase.from('team_aliases').select('team_id, alias');
    const aliasMap = buildAliasMap(aliases || []);
    console.log('Aliases loaded:', aliasMap.size);

    // Test specific match
    const testMatch = {
        homeTeam: "Man. City",
        awayTeam: "Chelsea", 
        date: "04.01.2026",
        odds: { home: 1.85, draw: 3.40, away: 4.10 }
    };

    const matched = findMatchingMatch(testMatch, dbMatches, aliasMap);
    console.log('\nMATCH RESULT:', matched ? `SUCCESS! ID=${matched.id}` : 'FAILED');
}

simulate();
