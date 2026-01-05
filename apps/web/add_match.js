// Add Leicester vs West Brom Match
const fs = require('fs');
const path = require('path');
const { createClient } = require('@supabase/supabase-js');

const envPath = path.join(__dirname, '.env.local');
const envContent = fs.readFileSync(envPath, 'utf8');
const env = {};
for (const line of envContent.split('\n')) {
  const idx = line.indexOf('=');
  if (idx > 0) {
    let value = line.substring(idx + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    env[line.substring(0, idx).trim()] = value;
  }
}

const supabase = createClient(env['SUPABASE_URL'], env['SUPABASE_SERVICE_KEY']);

async function addMatch() {
  // IDs from previous run
  const LEICESTER_ID = 161;
  const WEST_BROM_ID = 162;
  const CHAMPIONSHIP_LEAGUE_ID = 3;
  
  // Match time: Today at 23:00 (from Iddaa screenshot)
  const matchDate = new Date();
  matchDate.setHours(23, 0, 0, 0);

  const { data: existing } = await supabase
    .from('matches')
    .select('id')
    .eq('home_team_id', LEICESTER_ID)
    .eq('away_team_id', WEST_BROM_ID)
    .single();

  if (existing) {
    console.log('Match already exists with ID:', existing.id);
    return;
  }

  const { data, error } = await supabase
    .from('matches')
    .insert({
      home_team_id: LEICESTER_ID,
      away_team_id: WEST_BROM_ID,
      league_id: CHAMPIONSHIP_LEAGUE_ID,
      match_date: matchDate.toISOString(),
      status: 'scheduled',
      venue: 'King Power Stadium',
      external_id: '2558014'  // Iddaa event ID for reference
    })
    .select('id')
    .single();

  if (error) {
    console.error('Error adding match:', error.message);
    return;
  }

  console.log('Added Leicester vs West Brom match with ID:', data.id);
}

addMatch().catch(console.error);
