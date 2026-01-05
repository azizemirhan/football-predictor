
const fs = require('fs');
const path = '/home/aziz/.gemini/antigravity/brain/5bae58cd-3463-46fa-b376-8a20561c480b/nesine_pre_full.json';
try {
  const raw = fs.readFileSync(path, 'utf8');
  const data = JSON.parse(raw);
  
  if (data.sg && data.sg.EA) {
      // Find a football match with Home and Away teams
      const match = data.sg.EA.find(e => e.HN && e.AN && e.MA && e.MA.length > 0);
      
      if (match) {
          console.log('Match Found:', match.ENN || (match.HN + ' - ' + match.AN));
          console.log('Home:', match.HN);
          console.log('Away:', match.AN);
          console.log('Date:', match.D, match.T);
          console.log('League Ref:', match.LID || match.LC); // League ID?

          // List Markets
          console.log('Markets (First 10):');
          match.MA.slice(0, 10).forEach(m => {
              console.log(`  Market [${m.MN || 'Unknown'}] (MTID: ${m.MTID}) - Outcomes: ${m.OCA ? m.OCA.length : 0}`);
              if (m.OCA) {
                  console.log(`    Outcomes: ${m.OCA.map(o => `${o.N}:${o.O}`).join(', ')}`);
              }
          });
      } else {
          console.log('No suitable match found.');
      }
  }
} catch (e) {
  console.error(e);
}
