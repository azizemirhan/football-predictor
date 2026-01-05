const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

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

// Premier League team aliases for Nesine
// Format: { api_football_name: [nesine_variations] }
const NESINE_ALIASES = {
    'Manchester City': ['Man. City', 'Manchester City', 'M. City'],
    'Manchester United': ['Man. United', 'Manchester United', 'M. United', 'Man Utd'],
    'Liverpool': ['Liverpool'],
    'Arsenal': ['Arsenal'],
    'Chelsea': ['Chelsea'],
    'Tottenham': ['Tottenham', 'Spurs'],
    'Newcastle': ['Newcastle', 'Newcastle United'],
    'Brighton': ['Brighton', 'Brighton Hove'],
    'Aston Villa': ['Aston Villa', 'A. Villa'],
    'West Ham': ['West Ham', 'West Ham United'],
    'Brentford': ['Brentford'],
    'Fulham': ['Fulham'],
    'Crystal Palace': ['Crystal Palace', 'C. Palace'],
    'Everton': ['Everton'],
    'Nottingham Forest': ['Nottingham', 'Nott. Forest', 'Nottingham Forest'],
    'Wolves': ['Wolves', 'Wolverhampton'],
    'Bournemouth': ['Bournemouth', 'AFC Bournemouth'],
    'Burnley': ['Burnley'],
    'Leeds': ['Leeds', 'Leeds United'],
    'Sunderland': ['Sunderland']
};

async function seedAliases() {
    console.log('Fetching teams from DB...');
    
    // Get all teams
    const { data: teams, error } = await supabase
        .from('teams')
        .select('id, name');
    
    if (error) {
        console.error('Error fetching teams:', error);
        return;
    }
    
    console.log(`Found ${teams.length} teams in DB.`);
    
    // First, create the table if it doesn't exist
    console.log('\nCreating team_aliases table (if not exists)...');
    const { error: tableError } = await supabase.rpc('exec_sql', {
        sql: `
            CREATE TABLE IF NOT EXISTS team_aliases (
                id SERIAL PRIMARY KEY,
                team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
                alias VARCHAR(100) NOT NULL,
                source VARCHAR(50) DEFAULT 'nesine',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE(team_id, alias)
            );
        `
    });
    
    // If RPC doesn't exist, we'll just try to insert directly
    // The table should exist from migration
    
    let insertedCount = 0;
    const aliasesToInsert = [];
    
    for (const team of teams) {
        const aliases = NESINE_ALIASES[team.name];
        if (aliases) {
            for (const alias of aliases) {
                aliasesToInsert.push({
                    team_id: team.id,
                    alias: alias,
                    source: 'nesine'
                });
            }
        }
    }
    
    console.log(`Prepared ${aliasesToInsert.length} aliases to insert.`);
    
    // Insert all aliases (upsert to avoid duplicates)
    for (const aliasData of aliasesToInsert) {
        const { error: insertError } = await supabase
            .from('team_aliases')
            .upsert(aliasData, { onConflict: 'team_id, alias' });
        
        if (!insertError) {
            insertedCount++;
        } else if (!insertError.message.includes('duplicate')) {
            console.error('Insert error:', insertError.message);
        }
    }
    
    console.log(`\nInserted ${insertedCount} aliases.`);
    
    // Show sample
    const { data: sample } = await supabase
        .from('team_aliases')
        .select('*, teams(name)')
        .limit(10);
    
    console.log('\nSample aliases:');
    sample?.forEach(a => console.log(`  ${a.teams?.name} -> "${a.alias}"`));
}

seedAliases();
