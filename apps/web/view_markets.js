const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

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

async function viewMarkets() {
    // Get MATCH_RESULT market for Man City vs Chelsea (match_id: 630)
    const { data: markets, error } = await supabase
        .from('match_markets')
        .select('*')
        .eq('match_id', 630)
        .eq('market_type', 'MATCH_RESULT');
    
    if (error) return console.error('Error:', error);
    
    console.log(`Found ${markets.length} MATCH_RESULT markets for match 630:\n`);
    
    for (const m of markets) {
        console.log(`Bookmaker: ${m.bookmaker}`);
        console.log(`Outcomes (${m.outcomes.length}):`);
        m.outcomes.forEach(o => console.log(`  name="${o.name}" odds=${o.odds}`));
    }
}

viewMarkets();
