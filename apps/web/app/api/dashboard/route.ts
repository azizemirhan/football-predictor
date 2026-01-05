import { NextResponse } from 'next/server'
import { getSupabaseAdmin } from '@/lib/supabase/client'

export async function GET() {
  try {
    const supabase = getSupabaseAdmin()
    
    // Get match counts
    const { count: totalMatches } = await supabase
      .from('matches')
      .select('id', { count: 'exact', head: true })
    
    const { count: upcomingMatches } = await supabase
      .from('matches')
      .select('id', { count: 'exact', head: true })
      .eq('status', 'scheduled')
    
    const { count: liveMatches } = await supabase
      .from('matches')
      .select('id', { count: 'exact', head: true })
      .eq('status', 'live')
    
    // Get team count
    const { count: totalTeams } = await supabase
      .from('teams')
      .select('id', { count: 'exact', head: true })
    
    // Get value bets
    const { data: valueBets } = await supabase
      .from('value_bets')
      .select('edge, result')
    
    const activeValueBets = valueBets?.filter(vb => vb.result === 'pending') || []
    const avgEdge = activeValueBets.length > 0 
      ? activeValueBets.reduce((sum, vb) => sum + (vb.edge || 0), 0) / activeValueBets.length
      : 0
    
    // Get odds count
    const { count: totalOdds } = await supabase
      .from('odds')
      .select('id', { count: 'exact', head: true })
    
    // Get upcoming matches with teams
    const { data: upcomingMatchesData } = await supabase
      .from('matches')
      .select(`
        id,
        match_date,
        status,
        home_team:teams!matches_home_team_id_fkey(name, short_name, elo_rating, logo_url),
        away_team:teams!matches_away_team_id_fkey(name, short_name, elo_rating, logo_url)
      `)
      .eq('status', 'scheduled')
      .order('match_date', { ascending: true })
      .limit(5)
    
    // Format upcoming matches with predictions
    const formattedMatches = upcomingMatchesData?.map(match => {
      const homeTeam = match.home_team as any
      const awayTeam = match.away_team as any
      const homeElo = homeTeam?.elo_rating || 1500
      const awayElo = awayTeam?.elo_rating || 1500
      
      const eloDiff = homeElo - awayElo + 100
      const homeProb = 1 / (1 + Math.pow(10, -eloDiff / 400))
      const drawProb = 0.25
      const awayProb = Math.max(0.1, 1 - homeProb - drawProb)
      
      const matchDate = new Date(match.match_date)
      
      return {
        id: match.id,
        homeTeam: homeTeam?.short_name || 'Home',
        homeTeamFull: homeTeam?.name || 'Home Team',
        homeTeamLogo: homeTeam?.logo_url,
        awayTeam: awayTeam?.short_name || 'Away',
        awayTeamFull: awayTeam?.name || 'Away Team',
        awayTeamLogo: awayTeam?.logo_url,
        date: matchDate.toLocaleDateString('tr-TR'),
        time: matchDate.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }),
        prediction: {
          home: Math.round(homeProb * 100),
          draw: Math.round(drawProb * 100),
          away: Math.round(awayProb * 100)
        },
        confidence: homeProb > 0.6 || awayProb > 0.6 ? 'high' : 'medium'
      }
    }) || []
    
    // Get top value bets
    const { data: topValueBets } = await supabase
      .from('value_bets')
      .select(`
        id,
        selection,
        market_odds,
        edge,
        kelly_stake,
        match:matches(
          home_team:teams!matches_home_team_id_fkey(short_name),
          away_team:teams!matches_away_team_id_fkey(short_name)
        )
      `)
      .eq('result', 'pending')
      .order('edge', { ascending: false })
      .limit(3)
    
    const formattedValueBets = topValueBets?.map(vb => {
      const match = vb.match as any
      return {
        id: vb.id,
        match: `${match?.home_team?.short_name || '?'} vs ${match?.away_team?.short_name || '?'}`,
        selection: vb.selection,
        odds: vb.market_odds,
        edge: vb.edge,
        kellyStake: vb.kelly_stake
      }
    }) || []
    
    return NextResponse.json({
      stats: {
        totalMatches: totalMatches || 0,
        upcomingMatches: upcomingMatches || 0,
        liveMatches: liveMatches || 0,
        totalTeams: totalTeams || 0,
        totalOdds: totalOdds || 0,
        activeValueBets: activeValueBets.length,
        avgEdge: avgEdge
      },
      upcomingMatches: formattedMatches,
      topValueBets: formattedValueBets,
      lastUpdated: new Date().toISOString()
    })
  } catch (error) {
    console.error('Dashboard API error:', error)
    return NextResponse.json({ error: String(error) }, { status: 500 })
  }
}
