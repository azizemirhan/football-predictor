const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

// Load env
const envPath = path.resolve(__dirname, '.env.local');
const envContent = fs.readFileSync(envPath, 'utf8');
envContent.split('\n').forEach(line => {
    const idx = line.indexOf('=');
    if (idx > 0) {
        process.env[line.substring(0, idx).trim()] = line.substring(idx + 1).trim();
    }
});

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

async function insertTestOdds() {
    console.log('Inserting test odds...');
    
    // Manchester City vs Wolves (ID: 654)
    const { error: e1 } = await supabase.from('odds').insert({
        match_id: 654,
        bookmaker: 'Nesine',
        market_type: '1X2',
        home_odds: 1.45,
        draw_odds: 4.50,
        away_odds: 6.25,
        recorded_at: new Date().toISOString()
    });
    console.log('Match 654:', e1 ? 'Error - ' + e1.message : 'OK');
    
    // Chelsea vs Brentford (ID: 644)
    const { error: e2 } = await supabase.from('odds').insert({
        match_id: 644,
        bookmaker: 'Nesine',
        market_type: '1X2',
        home_odds: 1.75,
        draw_odds: 3.60,
        away_odds: 4.80,
        recorded_at: new Date().toISOString()
    });
    console.log('Match 644:', e2 ? 'Error - ' + e2.message : 'OK');
    
    // Leeds vs Fulham (ID: 645)
    const { error: e3 } = await supabase.from('odds').insert({
        match_id: 645,
        bookmaker: 'Nesine',
        market_type: '1X2',
        home_odds: 2.10,
        draw_odds: 3.30,
        away_odds: 3.50,
        recorded_at: new Date().toISOString()
    });
    console.log('Match 645:', e3 ? 'Error - ' + e3.message : 'OK');
    
    console.log('Done!');
}

insertTestOdds();
