import { NextResponse } from 'next/server'
import { getSupabaseAdmin } from '@/lib/supabase/client'

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const supabase = getSupabaseAdmin()
    const externalId = params.id

    // First, find the internal match_id from external_id
    const { data: match, error: matchError } = await supabase
      .from('matches')
      .select('id')
      .eq('external_id', externalId)
      .single()

    if (matchError || !match) {
      return NextResponse.json({ error: 'Match not found' }, { status: 404 })
    }

    // Get all markets for this match
    const { data: markets, error } = await supabase
      .from('match_markets')
      .select('*')
      .eq('match_id', match.id)
      .order('market_type')

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 })
    }

    // Group markets by bookmaker
    const byBookmaker: Record<string, any[]> = {}
    for (const market of markets || []) {
      if (!byBookmaker[market.bookmaker]) {
        byBookmaker[market.bookmaker] = []
      }
      byBookmaker[market.bookmaker].push({
        marketType: market.market_type,
        mtid: market.mtid,
        outcomes: market.outcomes
      })
    }

    // Fallback: If no match_markets data, check legacy odds table
    if (Object.keys(byBookmaker).length === 0) {
      const { data: legacyOdds } = await supabase
        .from('odds')
        .select('*')
        .eq('match_id', match.id)

      if (legacyOdds && legacyOdds.length > 0) {
        for (const odd of legacyOdds) {
          const bookmaker = odd.bookmaker || 'Unknown'
          if (!byBookmaker[bookmaker]) {
            byBookmaker[bookmaker] = []
          }
          byBookmaker[bookmaker].push({
            marketType: 'MATCH_RESULT',
            mtid: 1,
            outcomes: [
              { name: '1', odds: odd.home_odds },
              { name: '0', odds: odd.draw_odds },
              { name: '2', odds: odd.away_odds }
            ]
          })
        }
      }
    }

    return NextResponse.json({
      matchId: match.id,
      externalId,
      markets: byBookmaker,
      totalMarkets: Object.values(byBookmaker).reduce((sum, arr) => sum + arr.length, 0)
    })
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 })
  }
}
