import { NextResponse } from 'next/server'
import { getTeams } from '@/lib/api/api-football'

export async function GET() {
  try {
    const key = process.env.RAPIDAPI_KEY || ''
    const teams = await getTeams()
    return NextResponse.json({ 
      success: true, 
      count: teams.length, 
      first: teams[0]?.team?.name 
    })
  } catch (e) {
    const key = process.env.RAPIDAPI_KEY || ''
    return NextResponse.json({ 
      error: String(e),
      keyDebug: {
        length: key.length,
        first3: key.substring(0, 3),
        last3: key.substring(key.length - 3),
        hasQuotes: key.includes('"') || key.includes("'")
      }
    }, { status: 500 })
  }
}
