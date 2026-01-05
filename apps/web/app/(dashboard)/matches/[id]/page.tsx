import { fetchApi, getPredictions } from '@/lib/api/api-football'
import { getSupabaseAdmin } from '@/lib/supabase/client'
import { MatchDetailsClient } from './client'
import { notFound } from 'next/navigation'

interface MatchPageProps {
  params: {
    id: string
  }
}

async function getMatchData(id: string) {
  try {
    // First try API-Football
    const fixtureData = await fetchApi('fixtures', { id })
    if (fixtureData && fixtureData.length > 0) {
      return fixtureData[0]
    }
    
    // Fallback: Try to find match in Supabase by external_id
    const supabase = getSupabaseAdmin()
    const { data: dbMatch } = await supabase
      .from('matches')
      .select(`
        id, match_date, home_score, away_score, status, venue, external_id,
        home_team:teams!matches_home_team_id_fkey(id, name, short_name, logo_url),
        away_team:teams!matches_away_team_id_fkey(id, name, short_name, logo_url),
        league:leagues(id, name)
      `)
      .eq('external_id', id)
      .single()
    
    if (dbMatch) {
      // Convert to API-Football format for compatibility
      const homeTeam = Array.isArray(dbMatch.home_team) ? dbMatch.home_team[0] : dbMatch.home_team
      const awayTeam = Array.isArray(dbMatch.away_team) ? dbMatch.away_team[0] : dbMatch.away_team
      return {
        fixture: {
          id: dbMatch.id,
          date: dbMatch.match_date,
          status: { long: dbMatch.status || 'Scheduled', short: 'NS', elapsed: null },
          venue: { name: dbMatch.venue || 'TBD' }
        },
        teams: {
          home: { id: homeTeam?.id, name: homeTeam?.name || 'Unknown', logo: homeTeam?.logo_url || '' },
          away: { id: awayTeam?.id, name: awayTeam?.name || 'Unknown', logo: awayTeam?.logo_url || '' }
        },
        goals: { home: dbMatch.home_score, away: dbMatch.away_score },
        league: { id: dbMatch.league?.id, name: dbMatch.league?.name || 'Unknown' },
        _fromDb: true
      }
    }
    
    return null
  } catch (error) {
    console.error('Error fetching match:', error)
    return null
  }
}

export default async function MatchPage({ params }: MatchPageProps) {
  const match = await getMatchData(params.id)

  if (!match) {
    notFound()
  }

  // Fetch additional data in parallel
  const [injuries, stats, lineups, predictions] = await Promise.all([
    fetchApi('injuries', { fixture: params.id }),
    fetchApi('fixtures/statistics', { fixture: params.id }),
    fetchApi('fixtures/lineups', { fixture: params.id }),
    getPredictions(Number(params.id))
  ])

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-card rounded-lg p-6 border shadow-sm">
        <div className="flex items-center justify-between">
          <div className="text-center w-1/3">
            <img 
              src={match.teams.home.logo} 
              alt={match.teams.home.name} 
              className="w-20 h-20 mx-auto mb-2 object-contain"
            />
            <h2 className="text-xl font-bold">{match.teams.home.name}</h2>
            <a 
              href={`/teams/${match.teams.home.id}`}
              className="inline-block mt-2 text-xs px-3 py-1 bg-emerald-500/10 text-emerald-500 rounded-full hover:bg-emerald-500/20 transition-colors"
            >
              Takım Profili
            </a>
          </div>
          <div className="text-center flex flex-col items-center">
            <div className="text-4xl font-bold mb-1">
              {match.goals.home ?? '-'} : {match.goals.away ?? '-'}
            </div>
            <div className="text-sm text-muted-foreground uppercase tracking-wider font-semibold">
              {match.fixture.status.long}
              {match.fixture.status.elapsed && match.fixture.status.long === 'Second Half' && ` • ${match.fixture.status.elapsed}'`}
              {match.fixture.status.elapsed && match.fixture.status.long === 'First Half' && ` • ${match.fixture.status.elapsed}'`}
               {/* Or simpler: show elapsed if available and not FT/NS */}
               {['1H', 'HT', '2H', 'ET', 'P', 'BT', 'LIVE'].includes(match.fixture.status.short) && match.fixture.status.elapsed && (
                  <span className="text-red-500 animate-pulse ml-2">{match.fixture.status.elapsed}'</span>
               )}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {new Date(match.fixture.date).toLocaleString('tr-TR', {
                day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit'
              })}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {match.fixture.venue.name}
            </div>
          </div>
          <div className="text-center w-1/3">
            <img 
              src={match.teams.away.logo} 
              alt={match.teams.away.name} 
              className="w-20 h-20 mx-auto mb-2 object-contain"
            />
            <h2 className="text-xl font-bold">{match.teams.away.name}</h2>
            <a 
              href={`/teams/${match.teams.away.id}`}
              className="inline-block mt-2 text-xs px-3 py-1 bg-emerald-500/10 text-emerald-500 rounded-full hover:bg-emerald-500/20 transition-colors"
            >
              Takım Profili
            </a>
          </div>
        </div>
      </div>

      {/* Tabs Content */}
      <MatchDetailsClient 
        fixture={match}
        injuries={injuries}
        stats={stats}
        lineups={lineups}
        predictions={predictions}
        fixtureId={params.id}
      />
    </div>
  )
}
