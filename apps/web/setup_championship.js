// Add Championship League and Team Aliases
const fs = require('fs');
const path = require('path');
const { createClient } = require('@supabase/supabase-js');

// Load env properly
const envPath = path.join(__dirname, '.env.local');
const envContent = fs.readFileSync(envPath, 'utf8');
const env = {};
for (const line of envContent.split('\n')) {
  const idx = line.indexOf('=');
  if (idx > 0) {
    let value = line.substring(idx + 1).trim();
    // Remove quotes if present
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    env[line.substring(0, idx).trim()] = value;
  }
}

console.log('URL:', env['SUPABASE_URL'] ? 'Found' : 'Missing');
console.log('KEY:', env['SUPABASE_SERVICE_KEY'] ? 'Found' : 'Missing');

const supabase = createClient(
  env['SUPABASE_URL'],
  env['SUPABASE_SERVICE_KEY']
);

async function setupChampionship() {
  // 1. Check if Championship league exists
  const { data: existingLeague } = await supabase
    .from('leagues')
    .select('id')
    .eq('name', 'Championship')
    .single();

  let leagueId;
  if (!existingLeague) {
    // Add Championship league
    const { data: newLeague, error } = await supabase
      .from('leagues')
      .insert({
        name: 'Championship',
        country: 'England',
        external_id: '40',  // API-Football Championship ID
        logo_url: 'https://media.api-sports.io/football/leagues/40.png'
      })
      .select('id')
      .single();
    
    if (error) {
      console.error('Error adding Championship league:', error);
      return;
    }
    leagueId = newLeague.id;
    console.log('Added Championship league with ID:', leagueId);
  } else {
    leagueId = existingLeague.id;
    console.log('Championship league already exists with ID:', leagueId);
  }

  // 2. Add team aliases for Championship teams (Iddaa naming)
  const championshipAliases = [
    // Leicester City
    { team_name: 'Leicester City', aliases: ['Leicester City', 'Leicester', 'Lei', 'LCFC'] },
    // West Bromwich Albion
    { team_name: 'West Bromwich Albion', aliases: ['West Bromwich', 'West Brom', 'WBA', 'W. Bromwich'] },
    // Other popular Championship teams
    { team_name: 'Leeds United', aliases: ['Leeds', 'Leeds Utd', 'LUFC'] },
    { team_name: 'Burnley', aliases: ['Burnley FC'] },
    { team_name: 'Sheffield United', aliases: ['Sheffield Utd', 'Sheff Utd', 'SUFC'] },
  ];

  for (const team of championshipAliases) {
    // Find team ID
    const { data: teamData } = await supabase
      .from('teams')
      .select('id')
      .eq('name', team.team_name)
      .single();

    if (teamData) {
      for (const alias of team.aliases) {
        const { error } = await supabase
          .from('team_aliases')
          .upsert({
            team_id: teamData.id,
            alias: alias
          }, { onConflict: 'team_id, alias' });

        if (!error) {
          console.log(`Added alias "${alias}" for ${team.team_name}`);
        }
      }
    } else {
      console.log(`Team not found: ${team.team_name}`);
    }
  }

  console.log('Championship setup complete!');
}

setupChampionship().catch(console.error);
