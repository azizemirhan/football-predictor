import { NextResponse } from 'next/server'
import { getSupabaseAdmin } from '@/lib/supabase/client'
export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    const supabase = getSupabaseAdmin()
    
    // Get only upcoming matches (today and future)
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const { data: matches, error } = await supabase
      .from('matches')
      .select(`
        id,
        match_date,
        home_score,
        away_score,
        status,
        minute,
        venue,
        external_id,
        home_team:teams!matches_home_team_id_fkey(id, name, short_name, logo_url, elo_rating),
        away_team:teams!matches_away_team_id_fkey(id, name, short_name, logo_url, elo_rating),
        league:leagues(id, name),
        odds(bookmaker, market_type, home_odds, draw_odds, away_odds, recorded_at),
        match_markets(bookmaker, market_type, mtid, outcomes, recorded_at)
      `)
      .gte('match_date', today.toISOString())
      .order('match_date', { ascending: true })
      .limit(50)
    
    if (error) {
      console.error('Supabase error:', error)
      return NextResponse.json({ error: error.message }, { status: 500 })
    }
    
    // Transform data for frontend
    const formattedMatches = matches?.map(match => {
      const matchDate = new Date(match.match_date)
      
      // Generate simple prediction based on Elo ratings
      const homeTeam = match.home_team as any
      const awayTeam = match.away_team as any
      const homeElo = homeTeam?.elo_rating || 1500
      const awayElo = awayTeam?.elo_rating || 1500
      
      // Simple Elo-based probability calculation
      const eloDiff = homeElo - awayElo + 100 // Home advantage
      const homeWinProb = 1 / (1 + Math.pow(10, -eloDiff / 400))
      const drawProb = 0.25 // Simplified
      const awayWinProb = 1 - homeWinProb - drawProb
      
      // Get first available odds (prefer Nesine) for backward compat
      const matchOdds = match.odds as any[] | null;
      const nesineOdds = matchOdds?.find((o: any) => o.bookmaker === 'Nesine' && o.market_type === '1X2');
      const anyOdds = matchOdds?.[0];
      const selectedOdds = nesineOdds || anyOdds;
      
      // Build allOdds from match_markets (MATCH_RESULT only for main display)
      const markets = match.match_markets as any[] | null;
      const matchResultMarkets = markets?.filter((m: any) => m.market_type === 'MATCH_RESULT') || [];
      const allOdds = matchResultMarkets.map((m: any) => {
        const outcomes = m.outcomes as any[];
        // Different bookmakers use different outcome names:
        // Nesine: 1 (home), 2 (draw), 3 (away)
        // Iddaa:  1 (home), 0 (draw), 2 (away)
        let homeOdds = 0, drawOdds = 0, awayOdds = 0;
        
        if (m.bookmaker === 'Iddaa') {
          homeOdds = outcomes?.find((o: any) => o.name === '1')?.odds || 0;
          drawOdds = outcomes?.find((o: any) => o.name === '0')?.odds || 0;
          awayOdds = outcomes?.find((o: any) => o.name === '2')?.odds || 0;
        } else {
          // Nesine and others
          homeOdds = outcomes?.find((o: any) => o.name === '1')?.odds || 0;
          drawOdds = outcomes?.find((o: any) => o.name === '2')?.odds || 0;
          awayOdds = outcomes?.find((o: any) => o.name === '3')?.odds || 0;
        }
        
        return {
          bookmaker: m.bookmaker,
          home: homeOdds,
          draw: drawOdds,
          away: awayOdds
        };
      });
      
      return {
        id: match.id,
        externalId: match.external_id,
        homeTeam: homeTeam?.name || 'Unknown',
        homeTeamShort: homeTeam?.short_name || 'UNK',
        homeTeamLogo: homeTeam?.logo_url,
        awayTeam: awayTeam?.name || 'Unknown',
        awayTeamShort: awayTeam?.short_name || 'UNK',
        awayTeamLogo: awayTeam?.logo_url,
        date: matchDate.toISOString().split('T')[0],
        time: matchDate.toTimeString().slice(0, 5),
        venue: match.venue || 'TBD',
        status: match.status,
        homeScore: match.home_score,
        awayScore: match.away_score,
        minute: match.minute,
        league: (match.league as any)?.name || 'Premier League',
        prediction: {
          homeWin: Math.max(0.1, Math.min(0.8, homeWinProb)),
          draw: drawProb,
          awayWin: Math.max(0.1, Math.min(0.8, awayWinProb))
        },
        odds: selectedOdds ? {
          home: selectedOdds.home_odds,
          draw: selectedOdds.draw_odds,
          away: selectedOdds.away_odds,
          bookmaker: selectedOdds.bookmaker
        } : null,
        allOdds: allOdds.length > 0 ? allOdds : undefined
      }
    }) || []
    
    return NextResponse.json({
      matches: formattedMatches,
      total: formattedMatches.length,
      stats: {
        live: formattedMatches.filter(m => m.status === 'live').length,
        upcoming: formattedMatches.filter(m => m.status === 'scheduled').length,
        finished: formattedMatches.filter(m => m.status === 'finished').length
      }
    })
  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({ error: String(error) }, { status: 500 })
  }
}
