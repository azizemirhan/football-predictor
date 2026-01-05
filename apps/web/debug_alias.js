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

async function debug() {
    // 1. Get a specific Nesine match
    const scrapedMatch = {
        homeTeam: "Man. City",
        awayTeam: "Chelsea",
        date: "04.01.2026"  // DD.MM.YYYY
    };
    
    console.log('Testing match:', scrapedMatch.homeTeam, 'vs', scrapedMatch.awayTeam, 'on', scrapedMatch.date);
    
    // 2. Get DB matches
    const { data: dbMatches, error } = await supabase
        .from('matches')
        .select(`
            id, match_date,
            home_team:teams!matches_home_team_id_fkey(id, name),
            away_team:teams!matches_away_team_id_fkey(id, name)
        `)
        .gte('match_date', '2026-01-04')
        .lte('match_date', '2026-01-05');
    
    if (error) return console.error('DB Error:', error);
    
    console.log('DB Matches on 04.01:', dbMatches.length);
    dbMatches.forEach(m => {
        console.log(`  [ID: ${m.id}] ${m.home_team?.name} (ID:${m.home_team?.id}) vs ${m.away_team?.name} (ID:${m.away_team?.id})`);
    });
    
    // 3. Get aliases
    const { data: aliases } = await supabase.from('team_aliases').select('team_id, alias');
    console.log('\nTotal aliases:', aliases?.length);
    
    // Build alias map
    const aliasMap = new Map();
    (aliases || []).forEach(a => aliasMap.set(normalizeName(a.alias), a.team_id));
    
    console.log('\nAlias lookup for "man city":', aliasMap.get(normalizeName("Man. City")));
    console.log('Alias lookup for "chelsea":', aliasMap.get(normalizeName("Chelsea")));
    
    // 4. Manual date format check
    const dbMatch = dbMatches[0];
    if (dbMatch) {
        const dbDate = new Date(dbMatch.match_date);
        const day = String(dbDate.getDate()).padStart(2, '0');
        const month = String(dbDate.getMonth() + 1).padStart(2, '0');
        const year = dbDate.getFullYear();
        const formattedDbDate = `${day}.${month}.${year}`;
        console.log('\nDB date formatted:', formattedDbDate, '=== Scraped date:', scrapedMatch.date, '?', formattedDbDate === scrapedMatch.date);
    }
}

debug();
