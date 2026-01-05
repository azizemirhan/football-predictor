import { NextResponse } from 'next/server'
import { getSupabaseAdmin } from '@/lib/supabase/client'
import { scrapeTransfermarkt } from '@/lib/scraper/transfermarkt'

export const dynamic = 'force-dynamic'
export const maxDuration = 60 // Allow up to 60s for scraping

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const supabase = getSupabaseAdmin()
    const teamId = params.id

    // First, try to get team by internal ID
    let { data: team, error } = await supabase
      .from('teams')
      .select('id, name, short_name, logo_url, external_id, league_id, leagues(name)')
      .eq('id', teamId)
      .single()

    // If not found by internal ID, try external_id (API-Football ID)
    if (error || !team) {
      const { data: teamByExternal, error: extError } = await supabase
        .from('teams')
        .select('id, name, short_name, logo_url, external_id, league_id, leagues(name)')
        .eq('external_id', teamId)
        .single()
      
      if (extError || !teamByExternal) {
        return NextResponse.json({ error: 'Team not found' }, { status: 404 })
      }
      team = teamByExternal
    }

    if (!team) {
       return NextResponse.json({ error: 'Team not found' }, { status: 404 })
    }

    // All English League Transfermarkt Club IDs (with aliases for DB name matching)
    const tmClubIds: Record<string, number> = {
      // Premier League + Aliases
      'Arsenal': 11, 'Aston Villa': 405, 'Villa': 405,
      'Bournemouth': 989, 'AFC Bournemouth': 989,
      'Brentford': 1148, 'Brighton & Hove Albion': 1237, 'Brighton': 1237,
      'Chelsea': 631, 'Crystal Palace': 873,
      'Everton': 29, 'Fulham': 931,
      'Ipswich Town': 677, 'Ipswich': 677,
      'Liverpool': 31,
      'Manchester City': 281, 'Man City': 281,
      'Manchester United': 985, 'Man United': 985, 'Man Utd': 985,
      'Newcastle United': 762, 'Newcastle': 762,
      'Nottingham Forest': 703, 'Nottm Forest': 703,
      'Southampton': 180,
      'Tottenham Hotspur': 148, 'Tottenham': 148, 'Spurs': 148,
      'West Ham United': 379, 'West Ham': 379,
      'Wolverhampton Wanderers': 543, 'Wolverhampton': 543, 'Wolves': 543,
      // Championship + Aliases
      'Birmingham City': 337, 'Birmingham': 337,
      'Blackburn Rovers': 164, 'Blackburn': 164,
      'Bristol City': 1024, 'Bristol': 1024,
      'Burnley': 1132,
      'Cardiff City': 2593, 'Cardiff': 2593,
      'Coventry City': 354, 'Coventry': 354,
      'Derby County': 22, 'Derby': 22,
      'Hull City': 2602, 'Hull': 2602,
      'Leeds United': 399, 'Leeds': 399,
      'Leicester City': 1003, 'Leicester': 1003,
      'Luton Town': 1031, 'Luton': 1031,
      'Middlesbrough': 432, 'Millwall': 1577,
      'Norwich City': 1123, 'Norwich': 1123,
      'Oxford United': 1285, 'Oxford': 1285,
      'Plymouth Argyle': 334, 'Plymouth': 334,
      'Portsmouth': 718,
      'Preston North End': 1134, 'Preston': 1134,
      'Queens Park Rangers': 1039, 'QPR': 1039,
      'Sheffield United': 350, 'Sheffield Utd': 350,
      'Sheffield Wednesday': 867, 'Sheffield Wed': 867,
      'Stoke City': 512, 'Stoke': 512,
      'Sunderland': 289,
      'Swansea City': 2288, 'Swansea': 2288,
      'Watford': 1010,
      'West Bromwich Albion': 984, 'West Brom': 984, 'WBA': 984,
    }

    // All English League Transfermarkt Club IDs (with aliases for DB name matching)
    // Cast team to any to prevent TS errors on 'team.name'
    const tmClubId = (tmClubIds as any)[(team as any).name]
    if (!tmClubId) {
      // Return basic team data without Transfermarkt info
      return NextResponse.json({
        id: (team as any).id,
        name: (team as any).name,
        shortName: (team as any).short_name,
        logo: (team as any).logo_url,
        league: ((team as any).leagues as any)?.name || 'Unknown',
        squad: [],
        topScorers: [],
        topAssists: [],
        transfers: { arrivals: [], departures: [] },
        _source: 'database'
      })
    }

    // Verify team exists before scraping
    if (!team) {
       return NextResponse.json({ error: 'Team not found (unexpected null)' }, { status: 500 })
    }

    // Scrape Data (Parallel)
    // Cast team to any to avoid 'never' type inference issues
    const teamObj = team as any;
    
    const [tmData, sofascoreData] = await Promise.all([
      scrapeTransfermarkt(teamObj.name, tmClubId),
      import('@/lib/scraper/sofascore').then(async ({ getSofascoreId, scrapeSofascoreTeam }) => {
        try {
          // 1. Get Sofascore ID (search by name)
          // Use short_name for better search results if available, else name
          const searchName = teamObj.short_name && teamObj.short_name.length > 3 ? teamObj.short_name : teamObj.name;
          const sId = await getSofascoreId(searchName);
          
          if (sId) {
             return await scrapeSofascoreTeam(sId);
          }
          return null;
        } catch (e) {
          console.error('Sofascore scraping failed:', e);
          return null;
        }
      })
    ]);

    if (!tmData) {
      // Return basic data on scraping failure
       return NextResponse.json({
        id: teamObj.id,
        name: teamObj.name,
        shortName: teamObj.short_name,
        logo: teamObj.logo_url,
        league: (teamObj.leagues as any)?.name || 'Unknown',
        squad: [],
        topScorers: [],
        topAssists: [],
        transfers: { arrivals: [], departures: [] },
        sofascore: sofascoreData, // Return what we have
        _source: 'database_fallback',
        _error: 'Transfermarkt scraping failed'
      })
    }

    return NextResponse.json({
      id: teamObj.id,
      name: tmData.name || teamObj.name,
      shortName: teamObj.short_name,
      logo: tmData.logo || teamObj.logo_url,
      league: tmData.league || (teamObj.leagues as any)?.name || 'Unknown',
      squad: tmData.squad,
      topScorers: tmData.topScorers,
      topAssists: tmData.topAssists,
      transfers: tmData.transfers,
      clubInfo: tmData.clubInfo,
      sofascore: sofascoreData,
      _source: 'transfermarkt_sofascore'
    })
  } catch (error) {
    console.error('Team API Error:', error)
    return NextResponse.json({ error: String(error) }, { status: 500 })
  }
}
