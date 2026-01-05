const fs = require('fs');

// Load the RAW Nesine API response
const data = JSON.parse(fs.readFileSync('/home/aziz/.gemini/antigravity/brain/5bae58cd-3463-46fa-b376-8a20561c480b/nesine_pre_full.json', 'utf8'));

console.log('=== Nesine Market Type Analysis ===\n');

// Find football matches (TYPE: 1)
const footballMatches = data.sg?.EA?.filter(e => e.TYPE === 1) || [];
console.log(`Found ${footballMatches.length} football matches.\n`);

// Collect all unique market types
const marketTypes = new Map();

for (const match of footballMatches) {
    const markets = match.MA || [];
    for (const market of markets) {
        const mtid = market.MTID;
        const name = market.MN || 'Unknown';
        if (!marketTypes.has(mtid)) {
            marketTypes.set(mtid, {
                name,
                count: 1,
                sampleOutcomes: market.OCA?.map(o => `${o.N}:${o.ON || 'N/A'}:${o.O}`)?.slice(0, 5)
            });
        } else {
            marketTypes.get(mtid).count++;
        }
    }
}

// Sort by count (most common first)
const sorted = [...marketTypes.entries()].sort((a, b) => b[1].count - a[1].count);

console.log('Market Types Found:');
console.log('-------------------');
for (const [mtid, info] of sorted) {
    console.log(`\nMTID: ${mtid} - "${info.name}" (${info.count} matches)`);
    if (info.sampleOutcomes) {
        console.log(`  Outcomes: ${info.sampleOutcomes.join(' | ')}`);
    }
}

// Sample one match with all its markets
if (footballMatches.length > 0) {
    const sample = footballMatches.find(m => m.HN && m.AN && m.MA?.length > 5);
    if (sample) {
        console.log(`\n\n=== Sample Match: ${sample.HN} vs ${sample.AN} ===`);
        console.log(`Markets: ${sample.MA?.length}`);
        sample.MA?.slice(0, 15).forEach(m => {
            console.log(`  [MTID ${m.MTID}] ${m.MN}`);
        });
    }
}
