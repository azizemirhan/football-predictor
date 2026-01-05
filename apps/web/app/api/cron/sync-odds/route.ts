import { NextResponse } from 'next/server'
import { getSupabaseAdmin } from '@/lib/supabase/client'
import { NovadaClient } from '@/lib/scraper/novada'
import { scrapeNesine } from '@/lib/scraper/nesine'
import { scrapeIddaa } from '@/lib/scraper/iddaa'
import { findMatchingMatch, buildAliasMap } from '@/lib/scraper/utils'

// Vercel Cron protection - only allow requests with valid CRON_SECRET
export async function GET(request: Request) {
  // Verify cron secret (for production security)
  const authHeader = request.headers.get('authorization');
  if (process.env.CRON_SECRET && authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  console.log(`[CRON] Odds sync started at ${new Date().toISOString()}`);
  
  try {
    const supabase = getSupabaseAdmin()
    
    // 1. Fetch DB matches
    const today = new Date()
    const past = new Date(today); past.setDate(today.getDate() - 3);
    const future = new Date(today); future.setDate(today.getDate() + 14);
    
    const { data: dbMatches } = await supabase
      .from('matches')
      .select(`
        id, match_date, status,
        home_team:teams!matches_home_team_id_fkey(id, name),
        away_team:teams!matches_away_team_id_fkey(id, name)
      `)
      .gte('match_date', past.toISOString())
      .lte('match_date', future.toISOString())
    
    if (!dbMatches || dbMatches.length === 0) {
      console.log('[CRON] No upcoming matches in DB');
      return NextResponse.json({ message: 'No upcoming matches' })
    }
    
    // 2. Fetch team aliases
    const { data: aliases } = await supabase
      .from('team_aliases')
      .select('team_id, alias');
    
    const aliasMap = aliases ? buildAliasMap(aliases) : undefined;
    
    // Normalize DB matches
    const normalizedDbMatches = dbMatches.map((m: any) => ({
      ...m,
      home_team: Array.isArray(m.home_team) ? m.home_team[0] : m.home_team,
      away_team: Array.isArray(m.away_team) ? m.away_team[0] : m.away_team
    }));

    // 3. Run BOTH scrapers in parallel
    const client = new NovadaClient();
    const [nesineResult, iddaaResult] = await Promise.all([
      scrapeNesine(client),
      scrapeIddaa(client)
    ]);
    
    const results = {
      nesine: { scrapedCount: 0, matchesProcessed: 0, marketsProcessed: 0 },
      iddaa: { scrapedCount: 0, matchesProcessed: 0, marketsProcessed: 0 }
    };
    
    // 4. Process Nesine matches
    if (nesineResult.success && nesineResult.matches) {
      results.nesine.scrapedCount = nesineResult.matches.length;
      for (const scrapedMatch of nesineResult.matches) {
        const match = findMatchingMatch(scrapedMatch, normalizedDbMatches, aliasMap);
        if (match) {
          results.nesine.matchesProcessed++;
          for (const market of scrapedMatch.markets) {
            const { error } = await supabase.from('match_markets').upsert({
              match_id: match.id,
              bookmaker: 'Nesine',
              market_type: market.marketType,
              mtid: market.mtid,
              outcomes: market.outcomes,
              recorded_at: new Date().toISOString()
            }, { onConflict: 'match_id, bookmaker, market_type' });
            if (!error) results.nesine.marketsProcessed++;
          }
        }
      }
    }
    
    // 5. Process Iddaa matches
    if (iddaaResult.success && iddaaResult.matches) {
      results.iddaa.scrapedCount = iddaaResult.matches.length;
      for (const scrapedMatch of iddaaResult.matches) {
        const match = findMatchingMatch(scrapedMatch, normalizedDbMatches, aliasMap);
        if (match) {
          results.iddaa.matchesProcessed++;
          for (const market of scrapedMatch.markets) {
            const { error } = await supabase.from('match_markets').upsert({
              match_id: match.id,
              bookmaker: 'Iddaa',
              market_type: market.marketType,
              mtid: market.mtid,
              outcomes: market.outcomes,
              recorded_at: new Date().toISOString()
            }, { onConflict: 'match_id, bookmaker, market_type' });
            if (!error) results.iddaa.marketsProcessed++;
          }
        }
      }
    }
    
    console.log(`[CRON] Sync complete:`, results);
    
    return NextResponse.json({
      success: true,
      timestamp: new Date().toISOString(),
      results
    })
    
  } catch (error) {
    console.error('[CRON] Odds Sync Error:', error)
    return NextResponse.json({ error: String(error) }, { status: 500 })
  }
}

// Also allow POST for manual triggers
export { GET as POST }
