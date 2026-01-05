// Update Championship Team Logos
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

// Transfermarkt logo URL pattern: https://tmssl.akamaized.net/images/wappen/head/{club_id}.png
const teamLogos = [
  { id: 161, name: 'Leicester City', tm_id: 1003 },
  { id: 162, name: 'West Bromwich Albion', tm_id: 984 },
  { id: 164, name: 'Sheffield United', tm_id: 350 },
  { id: 165, name: 'Norwich City', tm_id: 1123 },
  { id: 166, name: 'Middlesbrough', tm_id: 432 },
  { id: 100, name: 'Sunderland', tm_id: 289 },
];

async function updateLogos() {
  for (const team of teamLogos) {
    const logoUrl = `https://tmssl.akamaized.net/images/wappen/head/${team.tm_id}.png`;
    
    const { error } = await supabase
      .from('teams')
      .update({ logo_url: logoUrl })
      .eq('id', team.id);
    
    if (error) {
      console.error(`Error updating ${team.name}:`, error.message);
    } else {
      console.log(`Updated ${team.name} logo: ${logoUrl}`);
    }
  }
  console.log('\nTeam logos updated!');
}

updateLogos().catch(console.error);
