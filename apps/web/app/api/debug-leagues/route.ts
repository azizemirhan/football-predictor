import { getSupabaseAdmin } from '@/lib/supabase/client'
import { NextResponse } from 'next/server'

export async function GET() {
  const supabase = getSupabaseAdmin()
  const { data: leagues, error } = await supabase.from('leagues').select('*')
  return NextResponse.json({ leagues, error })
}
