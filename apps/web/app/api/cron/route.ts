import { NextResponse } from 'next/server'

/**
 * Cron Job Endpoint
 * 
 * Bu endpoint periyodik olarak çağrılarak verileri günceller.
 * 
 * Kullanım seçenekleri:
 * 1. Vercel Cron (vercel.json ile)
 * 2. External cron service (cron-job.org, easycron.com)
 * 3. Supabase Edge Functions
 * 4. GitHub Actions scheduled workflow
 * 
 * Güvenlik: CRON_SECRET header'ı ile doğrulama
 */

const CRON_SECRET = process.env.CRON_SECRET || 'dev-secret'

export async function GET(request: Request) {
  // Verify cron secret for production
  const authHeader = request.headers.get('authorization')
  if (process.env.NODE_ENV === 'production' && authHeader !== `Bearer ${CRON_SECRET}`) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const startTime = Date.now()
  const results: Record<string, unknown> = {}

  try {
    // 1. Sync teams and matches from Football-Data.org
    const syncResponse = await fetch(`${getBaseUrl(request)}/api/sync`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'all' })
    })
    results.sync = await syncResponse.json()

    // Wait for rate limiting
    await new Promise(resolve => setTimeout(resolve, 2000))

    // 2. Generate/update odds
    const oddsResponse = await fetch(`${getBaseUrl(request)}/api/odds`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })
    results.odds = await oddsResponse.json()

    const duration = Date.now() - startTime

    return NextResponse.json({
      success: true,
      message: 'Cron job completed successfully',
      results,
      duration: `${duration}ms`,
      timestamp: new Date().toISOString()
    })
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: String(error),
      timestamp: new Date().toISOString()
    }, { status: 500 })
  }
}

function getBaseUrl(request: Request): string {
  const url = new URL(request.url)
  return `${url.protocol}//${url.host}`
}
