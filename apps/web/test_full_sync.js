const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');
const { distance } = require('fastest-levenshtein');

// Load env
const envPath = path.resolve(__dirname, '.env.local');
fs.readFileSync(envPath, 'utf8').split('\n').forEach(line => {
    const idx = line.indexOf('=');
    if (idx > 0) process.env[line.substring(0, idx).trim()] = line.substring(idx + 1).trim();
});

const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
);

function normalizeName(name) {
    if (!name) return '';
    return name.toLowerCase()
        .replace(/ü/g, 'u').replace(/ğ/g, 'g').replace(/ı/g, 'i')
        .replace(/ş/g, 's').replace(/ç/g, 'c').replace(/ö/g, 'o')
        .replace(/[^a-z0-9 ]/g, '').trim();
}

function buildAliasMap(aliases) {
    const map = new Map();
    for (const a of aliases) map.set(normalizeName(a.alias), a.team_id);
    return map;
}

function findMatchingMatch(scrapedMatch, dbMatches, aliasMap) {
    const scrapedDate = scrapedMatch.date;
    
    const sameDateMatches = dbMatches.filter(m => {
        const dbDate = new Date(m.match_date);
        const formattedDbDate = `${String(dbDate.getDate()).padStart(2,'0')}.${String(dbDate.getMonth()+1).padStart(2,'0')}.${dbDate.getFullYear()}`;
        return formattedDbDate === scrapedDate;
    });

    if (sameDateMatches.length === 0) return null;

    if (aliasMap) {
        const homeId = aliasMap.get(normalizeName(scrapedMatch.homeTeam));
        const awayId = aliasMap.get(normalizeName(scrapedMatch.awayTeam));
        if (homeId && awayId) {
            const exactMatch = sameDateMatches.find(m => m.home_team?.id === homeId && m.away_team?.id === awayId);
            if (exactMatch) return exactMatch;
        }
    }

    // Fuzzy fallback
    for (const dbMatch of sameDateMatches) {
        if (!dbMatch.home_team || !dbMatch.away_team) continue;
        const d1 = distance(normalizeName(scrapedMatch.homeTeam), normalizeName(dbMatch.home_team.name));
        const d2 = distance(normalizeName(scrapedMatch.awayTeam), normalizeName(dbMatch.away_team.name));
        if (d1 + d2 < 12) return dbMatch;
    }

    return null;
}

async function testSync() {
    console.log('=== Full API Route Simulation ===\n');
    
    // 1. Fetch DB matches (same as API)
    const today = new Date();
    const past = new Date(today); past.setDate(today.getDate() - 3);
    const future = new Date(today); future.setDate(today.getDate() + 14);
    
    console.log('Date range:', past.toISOString(), '->', future.toISOString());
    
    const { data: dbMatches } = await supabase
        .from('matches')
        .select(`id, match_date, status,
            home_team:teams!matches_home_team_id_fkey(id, name, elo_rating),
            away_team:teams!matches_away_team_id_fkey(id, name, elo_rating)`)
        .gte('match_date', past.toISOString())
        .lte('match_date', future.toISOString());

    // Normalize
    const normalizedDbMatches = dbMatches?.map(m => ({
        ...m,
        home_team: Array.isArray(m.home_team) ? m.home_team[0] : m.home_team,
        away_team: Array.isArray(m.away_team) ? m.away_team[0] : m.away_team
    })) || [];

    console.log('DB matches loaded:', normalizedDbMatches.length);

    // 2. Load aliases
    const { data: aliases } = await supabase.from('team_aliases').select('team_id, alias');
    const aliasMap = buildAliasMap(aliases || []);
    console.log('Aliases loaded:', aliasMap.size);

    // 3. Load saved scrape data (simulate what scraper returns)
    const scrapedMatches = JSON.parse(fs.readFileSync('/home/aziz/.gemini/antigravity/brain/5bae58cd-3463-46fa-b376-8a20561c480b/nesine_matches.json', 'utf8'));
    console.log('Scraped matches:', scrapedMatches.length);

    // 4. Match loop
    let matched = 0;
    for (const sm of scrapedMatches) {
        const match = findMatchingMatch(sm, normalizedDbMatches, aliasMap);
        if (match) {
            matched++;
            console.log(`MATCHED: ${sm.homeTeam} vs ${sm.awayTeam} -> DB ID ${match.id}`);
        }
    }

    console.log(`\nTOTAL MATCHED: ${matched} / ${scrapedMatches.length}`);
}

testSync();
