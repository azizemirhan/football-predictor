

// @ts-ignore
const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
// @ts-ignore
const { findMatchingMatch } = require('./lib/scraper/utils');
const path = require('path');

// Manually load env from .env.local
const envPath = path.resolve(process.cwd(), '.env.local');
const envContent = fs.readFileSync(envPath, 'utf8');
envContent.split('\n').forEach((line: string) => {
    const [key, val] = line.split('=');
    if (key && val) process.env[key.trim()] = val.trim();
});

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseKey) {
    console.error('Missing Supabase credentials');
    process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function run() {
    // 1. Load Scraped Matches (Fix path)
    const jsonPath = '/home/aziz/.gemini/antigravity/brain/5bae58cd-3463-46fa-b376-8a20561c480b/nesine_matches.json';
    const scrapedMatches = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
    console.log(`Loaded ${scrapedMatches.length} scraped matches.`);

    // 2. Fetch DB Matches
    const today = new Date();
    const past = new Date(today); past.setDate(today.getDate() - 3); 
    const future = new Date(today); future.setDate(today.getDate() + 30);
    
    console.log('Fetching DB matches between', past.toISOString(), 'and', future.toISOString());

    const { data: dbMatches, error } = await supabase
      .from('matches')
      .select(`
        id, 
        match_date,
        home_team:teams!matches_home_team_id_fkey(name),
        away_team:teams!matches_away_team_id_fkey(name)
      `)
      .gte('match_date', past.toISOString())
      .lte('match_date', future.toISOString());

    if (error) {
        console.error('DB Error:', error);
        return;
    }
    
    // Normalize DB Matches structure (handle array vs object)
    const normalizedDbMatches = dbMatches?.map((m: any) => ({
        ...m,
        home_team: Array.isArray(m.home_team) ? m.home_team[0] : m.home_team,
        away_team: Array.isArray(m.away_team) ? m.away_team[0] : m.away_team
    })) || [];

    console.log(`Fetched ${normalizedDbMatches.length} DB matches.`);
    
    // 3. Test Matching
    let matchedCount = 0;
    const failures: any[] = [];
    
    // Check specific match if user wants, or first 50
    // Try to find ANY match
    
    for (const sm of scrapedMatches) {
        // Skip if no date
        if (!sm.date) continue;

        const match = findMatchingMatch(sm, normalizedDbMatches);
        if (match) {
            matchedCount++;
            console.log(`[MATCH] ${sm.homeTeam} vs ${sm.awayTeam} -> DB: ${match.home_team.name} vs ${match.away_team.name}`);
        } else {
             const sameDateMatches = normalizedDbMatches.filter((m: any) => {
                  const dbDate = new Date(m.match_date);
                  const day = String(dbDate.getDate()).padStart(2, '0');
                  const month = String(dbDate.getMonth() + 1).padStart(2, '0');
                  const year = dbDate.getFullYear();
                  const formattedDbDate = `${day}.${month}.${year}`;
                  return formattedDbDate === sm.date;
             });
             
             if (sameDateMatches.length > 0) {
                 failures.push({
                     scraped: `${sm.homeTeam} - ${sm.awayTeam} (${sm.date})`,
                     potentialDB: sameDateMatches.map((m: any) => `${m.home_team.name} - ${m.away_team.name}`).join(' | ')
                 });
             }
        }
    }

    console.log(`Matched ${matchedCount} / ${scrapedMatches.length} total.`);
    console.log('Sample Failures (Date matched but names failed):');
    failures.slice(0, 50).forEach(f => console.log(JSON.stringify(f, null, 2)));
}

run();
