import { getSupabaseAdmin } from '@/lib/supabase/client'
import { NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

export async function GET() {
  const supabase = getSupabaseAdmin()
  const { count: matches } = await supabase.from('matches').select('*', { count: 'exact', head: true })
  const { count: teams } = await supabase.from('teams').select('*', { count: 'exact', head: true })
  
  return NextResponse.json({ matches, teams })
}
