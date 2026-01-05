import { NextResponse } from 'next/server'
import { getTeams, getFixtures, getStandings, ApiFootballMatch, ApiFootballTeam } from '@/lib/api/api-football'
import { getSupabaseAdmin } from '@/lib/supabase/client'

// Premier League ID in API-Football
const LEAGUE_ID = 39

// Helper to map API status to DB enum
function mapStatus(shortStatus: string): 'scheduled' | 'live' | 'finished' | 'postponed' | 'cancelled' {
  if (['FT', 'AET', 'PEN'].includes(shortStatus)) return 'finished'
  if (['NS', 'TBD', 'NA'].includes(shortStatus)) return 'scheduled'
  if (['1H', 'HT', '2H', 'ET', 'P', 'BT', 'LIVE'].includes(shortStatus)) return 'live'
  if (['PST'].includes(shortStatus)) return 'postponed'
  if (['CANC', 'ABD', 'AWD', 'WO'].includes(shortStatus)) return 'cancelled'
  return 'scheduled' // Default
}

export async function POST(request: Request) {
  try {
    const supabase = getSupabaseAdmin()
    const body = await request.json().catch(() => ({}))
    const { type = 'all', reset = false } = body

    // 0. Reset Tables if requested (Full Migration)
    if (reset) {
      console.log('Resetting database for migration...')
      await supabase.from('value_bets').delete().neq('id', 0)
      await supabase.from('odds').delete().neq('id', 0)
      await supabase.from('predictions').delete().neq('id', 0)
      await supabase.from('matches').delete().neq('id', 0)
      await supabase.from('teams').delete().neq('id', 0)
      // League?
    }

    // 1. Ensure League Exists
    let { data: league, error: findError } = await supabase
      .from('leagues')
      .select('id, external_id')
      .eq('external_id', String(LEAGUE_ID))
      .single()
    
    // If not found by ID, find by Name (Migration from 'PL' to '39')
    if (!league) {
      const { data: legacyLeague } = await supabase
        .from('leagues')
        .select('id')
        .eq('name', 'Premier League')
        .single()
      
      if (legacyLeague) {
        // Update legacy league
        await supabase
          .from('leagues')
          .update({ external_id: String(LEAGUE_ID) })
          .eq('id', legacyLeague.id)
        league = { id: legacyLeague.id, external_id: String(LEAGUE_ID) }
      }
    }
    
    let dbLeagueId = league?.id
    let leagueError = findError
    
    if (!league) {
      const { data: newLeague, error: createError } = await supabase
        .from('leagues')
        .insert({
          name: 'Premier League',
          external_id: String(LEAGUE_ID),
          country: 'England'
        })
        .select()
        .single()
      dbLeagueId = newLeague?.id
      if (createError) leagueError = createError
    }

    const results: Record<string, any> = { 
      success: true, 
      timestamp: new Date().toISOString(), 
      dbLeagueId,
      leagueError 
    }

    // 2. Sync Teams
    if (type === 'all' || type === 'teams') {
      const teams = await getTeams()
      let synced = 0
      
      const errors: any[] = []
      for (const t of teams) {
        const { error } = await supabase
          .from('teams')
          .upsert({
            name: t.team.name,
            short_name: t.team.code || t.team.name.substring(0, 3),
            logo_url: t.team.logo,
            external_id: t.team.id,
            league_id: dbLeagueId
          }, { onConflict: 'external_id' })
        
        if (!error) synced++
        else errors.push(error)
      }
      results.teams = { count: synced, total: teams.length, errors: errors.slice(0, 3) }
    }

    // 3. Sync Matches (Next 30 days and Last 7 days)
    if (type === 'all' || type === 'matches') {
      const today = new Date()
      const past = new Date(today)
      past.setDate(today.getDate() - 7)
      const future = new Date(today)
      future.setDate(today.getDate() + 30)
      
      const fixtures = await getFixtures(
        past.toISOString().split('T')[0],
        future.toISOString().split('T')[0]
      )
      
      let synced = 0
      const errors: any[] = []
      for (const f of fixtures) {
        // Find team IDs
        const { data: homeTeam } = await supabase.from('teams').select('id').eq('external_id', f.teams.home.id).single()
        const { data: awayTeam } = await supabase.from('teams').select('id').eq('external_id', f.teams.away.id).single()
        
        if (homeTeam && awayTeam) {


          const { error } = await supabase
            .from('matches')
            .upsert({
              external_id: f.fixture.id,
              league_id: dbLeagueId,
                  home_team_id: homeTeam.id,
                  away_team_id: awayTeam.id,
                  match_date: f.fixture.date,
                  status: mapStatus(f.fixture.status.short),
                  venue: f.fixture.venue.name,
                  home_score: f.goals.home,
              away_score: f.goals.away
            }, { onConflict: 'external_id' })
            
          if (!error) synced++
          else errors.push(error)
        }
      }
      results.matches = { count: synced, total: fixtures.length, errors: errors.slice(0, 3) }
    }

    // 3.1. Sync Live Matches (Specific efficient update)
    if (type === 'live') {
      const fixtures = await import('@/lib/api/api-football').then(m => m.getLiveFixtures())
      let synced = 0
      const errors: any[] = []
      
      for (const f of fixtures) {
        // Find team IDs (Assuming they exist, or skip)
        const { data: homeTeam } = await supabase.from('teams').select('id').eq('external_id', f.teams.home.id).single()
        const { data: awayTeam } = await supabase.from('teams').select('id').eq('external_id', f.teams.away.id).single()
        
        if (homeTeam && awayTeam) {
           const { error } = await supabase
            .from('matches')
            .upsert({
              external_id: f.fixture.id,
              league_id: dbLeagueId, // Might be risky if live match is different league. But we reset dbLeagueId above.
                                     // Actually getLiveFixtures in api-football.ts IS HARDCODED to LEAGUE_ID (39).
                                     // So using dbLeagueId is safe.
              home_team_id: homeTeam.id,
              away_team_id: awayTeam.id,
              match_date: f.fixture.date,
              status: mapStatus(f.fixture.status.short),
              venue: f.fixture.venue.name,
              home_score: f.goals.home,
              away_score: f.goals.away,
              minute: f.fixture.status.elapsed
            }, { onConflict: 'external_id' })
            
          if (!error) synced++
          else errors.push(error)
        }
      }
      results.live = { count: synced, total: fixtures.length, errors: errors.slice(0, 3) }
    }
    
    // 4. Update Standings (Elo defaults for now, or fetch API standings)
    if (type === 'all' || type === 'standings') {
      const standings = await getStandings()
      // Logic to update team Elo or stats could go here
      // For now we just log it
      results.standings = { count: standings.length }
    }

    return NextResponse.json(results)
  } catch (error) {
    console.error('Sync Error:', error)
    return NextResponse.json({ error: String(error) }, { status: 500 })
  }
}
