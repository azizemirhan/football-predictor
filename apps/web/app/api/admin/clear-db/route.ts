
import { getSupabaseAdmin } from '@/lib/supabase/client'
import { NextResponse } from 'next/server'

export async function POST() {
  const supabase = getSupabaseAdmin()
  
  // Delete in order of dependencies
  const { error: e1 } = await supabase.from('value_bets').delete().neq('id', 0)
  const { error: e2 } = await supabase.from('predictions').delete().neq('id', 0)
  const { error: e3 } = await supabase.from('odds').delete().neq('id', 0)
  // Matches depend on teams/leagues?
  const { error: e4 } = await supabase.from('matches').delete().neq('id', 0)
  // We keep Teams and Leagues usually, but if teams have legacy IDs?
  // Let's keep teams/leagues for now, assuming Sync updates them correctly.
  // Actually, teams might have legacy IDs too. 
  // API-Football teams have IDs like 33, 40 etc.
  // Football-Data teams have IDs like 62.
  // If IDs overlap?
  // API-Football Man Utd is 33. SQL ID 33.
  // Football-Data Man Utd was something else.
  // Better to clear TEAMS too if possible.
  
  const { error: e5 } = await supabase.from('teams').delete().neq('id', 0)
  const { error: e6 } = await supabase.from('leagues').delete().neq('id', 0)

  return NextResponse.json({ 
    success: true,
    message: 'Database cleared', 
    errors: [e1, e2, e3, e4, e5, e6].filter(Boolean) 
  })
}
