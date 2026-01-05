import { NextResponse } from 'next/server'
import { getSupabaseAdmin } from '@/lib/supabase/client'

/**
 * Sync Status API
 * 
 * Returns the last sync time and status for displaying in the UI
 */

// In-memory store for sync status (in production, use Redis or database)
let lastSyncStatus = {
  lastSync: null as string | null,
  status: 'idle' as 'idle' | 'running' | 'success' | 'error',
  results: null as Record<string, unknown> | null,
  error: null as string | null
}

export async function GET() {
  try {
    const supabase = getSupabaseAdmin()
    
    // Get counts
    const { count: matchCount } = await supabase
      .from('matches')
      .select('id', { count: 'exact', head: true })
    
    const { count: teamCount } = await supabase
      .from('teams')
      .select('id', { count: 'exact', head: true })
    
    const { count: oddsCount } = await supabase
      .from('odds')
      .select('id', { count: 'exact', head: true })
    
    const { count: valueBetCount } = await supabase
      .from('value_bets')
      .select('id', { count: 'exact', head: true })
      .eq('result', 'pending')
    
    // Get latest odds timestamp as proxy for last sync
    const { data: latestOdds } = await supabase
      .from('odds')
      .select('recorded_at')
      .order('recorded_at', { ascending: false })
      .limit(1)
      .single()
    
    return NextResponse.json({
      status: 'ok',
      lastSync: latestOdds?.recorded_at || null,
      counts: {
        matches: matchCount || 0,
        teams: teamCount || 0,
        odds: oddsCount || 0,
        valueBets: valueBetCount || 0
      },
      syncStatus: lastSyncStatus
    })
  } catch (error) {
    return NextResponse.json({
      status: 'error',
      error: String(error)
    }, { status: 500 })
  }
}

// POST - Update sync status (called by cron job)
export async function POST(request: Request) {
  try {
    const body = await request.json()
    
    lastSyncStatus = {
      lastSync: new Date().toISOString(),
      status: body.status || 'success',
      results: body.results || null,
      error: body.error || null
    }
    
    return NextResponse.json({ success: true })
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 })
  }
}
