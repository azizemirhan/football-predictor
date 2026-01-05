
const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');
const { distance } = require('fastest-levenshtein'); // Hope this works CJS

// Logic from utils.ts
function normalizeName(name) {
  if (!name) return '';
  return name.toLowerCase()
    .replace(/ü/g, 'u')
    .replace(/ğ/g, 'g')
    .replace(/ı/g, 'i')
    .replace(/ş/g, 's')
    .replace(/ç/g, 'c')
    .replace(/ö/g, 'o')
    .replace(/[^a-z0-9 ]/g, '') 
    .trim();
}

function findMatchingMatch(scrapedMatch, dbMatches) {
  const scrapedHome = normalizeName(scrapedMatch.homeTeam);
  const scrapedAway = normalizeName(scrapedMatch.awayTeam);
  const scrapedDate = scrapedMatch.date; // "DD.MM.YYYY"
  
  // 1. Filter by date first
  const sameDateMatches = dbMatches.filter(m => {
      const dbDate = new Date(m.match_date);
      const day = String(dbDate.getDate()).padStart(2, '0');
      const month = String(dbDate.getMonth() + 1).padStart(2, '0');
      const year = dbDate.getFullYear();
      const formattedDbDate = `${day}.${month}.${year}`;
      return formattedDbDate === scrapedDate;
  });

  if (sameDateMatches.length === 0) return null;

  // 2. Fuzzy match teams
  let bestMatch = null;
  let minDistance = Infinity;

  for (const dbMatch of sameDateMatches) {
      if (!dbMatch.home_team || !dbMatch.away_team) continue;
      
      const dbHome = normalizeName(dbMatch.home_team.name);
      const dbAway = normalizeName(dbMatch.away_team.name);
      
      const distHome = distance(scrapedHome, dbHome);
      const distAway = distance(scrapedAway, dbAway);
      const totalDist = distHome + distAway;
      
      if (scrapedHome.includes('man city')) {
          console.log(`DEBUG: Comparing "${scrapedHome}" vs "${dbHome}" (Dist: ${distHome}) AND "${scrapedAway}" vs "${dbAway}" (Dist: ${distAway}). Total: ${totalDist}`);
      }
      
      if (totalDist < 10 && totalDist < minDistance) {
          minDistance = totalDist;
          bestMatch = dbMatch;
      }
  }

  return bestMatch;
}

// Manually load env from .env.local
try {
    const envPath = path.resolve(__dirname, '.env.local');
    console.log('Loading env from:', envPath);
    
    if (fs.existsSync(envPath)) {
        const envContent = fs.readFileSync(envPath, 'utf8');
        envContent.split('\n').forEach(line => {
             const idx = line.indexOf('=');
             if (idx > 0) {
                 const key = line.substring(0, idx).trim();
                 let val = line.substring(idx + 1).trim();
                 // Remove quotes if present
                 if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
                     val = val.slice(1, -1);
                 }
                 process.env[key] = val;
             }
        });
        console.log('Env loaded.');
        console.log('NEXT_PUBLIC_SUPABASE_URL:', !!process.env.NEXT_PUBLIC_SUPABASE_URL);
        console.log('SUPABASE_SERVICE_ROLE_KEY:', !!process.env.SUPABASE_SERVICE_ROLE_KEY);
        console.log('NEXT_PUBLIC_SUPABASE_ANON_KEY:', !!process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY);
    } else {
        console.log('No .env.local found at', envPath);
    }
} catch (e) { console.log('Error loading env:', e); }

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
// Fallback to Anon key if Service key missing
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
    console.error('Missing Supabase credentials (URL or Key)');
    process.exit(1);
}

console.log('Initializing Supabase with key endpoint:', supabaseKey.substring(0, 10) + '...');
const supabase = createClient(supabaseUrl, supabaseKey);

async function run() {
    // 1. Load Scraped Matches
    const jsonPath = '/home/aziz/.gemini/antigravity/brain/5bae58cd-3463-46fa-b376-8a20561c480b/nesine_matches.json';
    const scrapedMatches = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
    console.log(`Loaded ${scrapedMatches.length} scraped matches.`);

    // 2. Fetch DB Matches
    const today = new Date();
    const past = new Date(today); past.setDate(today.getDate() - 5); 
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
    const normalizedDbMatches = dbMatches?.map(m => ({
        ...m,
        home_team: Array.isArray(m.home_team) ? m.home_team[0] : m.home_team,
        away_team: Array.isArray(m.away_team) ? m.away_team[0] : m.away_team
    })) || [];

    console.log(`Fetched ${normalizedDbMatches.length} DB matches.`);
    
    let matchedCount = 0;
    const failures = [];

    for (const sm of scrapedMatches) {
        if (!sm.date) continue;

        const match = findMatchingMatch(sm, normalizedDbMatches);
        if (match) {
            matchedCount++;
        } else {
             const sameDateMatches = normalizedDbMatches.filter(m => {
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
                     potentialDB: sameDateMatches.map(m => `${m.home_team.name} - ${m.away_team.name}`).join(' | ')
                 });
             }
        }
    }

    console.log(`Matched ${matchedCount} / ${scrapedMatches.length} total.`);
    console.log(`Sample Failures (${failures.length}):`);
    failures.slice(0, 50).forEach(f => console.log(JSON.stringify(f, null, 2)));
}

run();
