
import { getPlayerStats, getTeamStatistics } from './apps/web/lib/api/api-football';

async function test() {
  try {
    console.log('Fetching Team Stats...');
    const teamStats = await getTeamStatistics(50); // Man City
    console.log('Team Stats Keys:', Object.keys(teamStats || {}));
    if (teamStats) {
       console.log('Form:', teamStats.form);
       console.log('Goals:', JSON.stringify(teamStats.goals, null, 2));
    }

    console.log('\nFetching Player Stats...');
    const players = await getPlayerStats(50);
    if (players && players.length > 0) {
      console.log(`Found ${players.length} players`);
      const p = players[0];
      console.log('Sample Player:', p.player.name);
      console.log('Rating:', p.statistics[0].games.rating);
      console.log('Stats:', JSON.stringify(p.statistics[0], null, 2));
    } else {
      console.log('No players found');
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

test();
