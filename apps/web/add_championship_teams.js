// Add Championship Teams
const fs = require('fs');
const path = require('path');
const { createClient } = require('@supabase/supabase-js');

// Load env
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

// Championship League ID
const CHAMPIONSHIP_LEAGUE_ID = 3;

const championshipTeams = [
  { name: 'Leicester City', short_name: 'LEI', external_id: '46', aliases: ['Leicester City', 'Leicester', 'Lei', 'LCFC'] },
  { name: 'West Bromwich Albion', short_name: 'WBA', external_id: '60', aliases: ['West Bromwich', 'West Brom', 'WBA', 'W. Bromwich'] },
  { name: 'Leeds United', short_name: 'LEE', external_id: '63', aliases: ['Leeds', 'Leeds Utd', 'LUFC'] },
  { name: 'Sheffield United', short_name: 'SHU', external_id: '62', aliases: ['Sheffield Utd', 'Sheff Utd', 'SUFC'] },
  { name: 'Sunderland', short_name: 'SUN', external_id: '71', aliases: ['Sunderland AFC', 'SAFC'] },
  { name: 'Norwich City', short_name: 'NOR', external_id: '68', aliases: ['Norwich', 'NCFC'] },
  { name: 'Middlesbrough', short_name: 'MID', external_id: '67', aliases: ['Middlesbrough FC', 'Boro'] },
];

async function addTeams() {
  for (const team of championshipTeams) {
    // Check if team exists
    const { data: existing } = await supabase
      .from('teams')
      .select('id')
      .eq('name', team.name)
      .single();

    let teamId;
    if (existing) {
      teamId = existing.id;
      console.log(`Team exists: ${team.name} (ID: ${teamId})`);
    } else {
      // Add team
      const { data: newTeam, error } = await supabase
        .from('teams')
        .insert({
          name: team.name,
          short_name: team.short_name,
          external_id: team.external_id,
          league_id: CHAMPIONSHIP_LEAGUE_ID
        })
        .select('id')
        .single();

      if (error) {
        console.error(`Error adding ${team.name}:`, error.message);
        continue;
      }
      teamId = newTeam.id;
      console.log(`Added team: ${team.name} (ID: ${teamId})`);
    }

    // Add aliases
    for (const alias of team.aliases) {
      const { error } = await supabase
        .from('team_aliases')
        .upsert({ team_id: teamId, alias }, { onConflict: 'team_id, alias' });
      
      if (!error) {
        console.log(`  + alias: "${alias}"`);
      }
    }
  }
  console.log('\nChampionship teams setup complete!');
}

addTeams().catch(console.error);
