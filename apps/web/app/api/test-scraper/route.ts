
import { NextResponse } from 'next/server'
import { NovadaClient } from '@/lib/scraper/novada'
import { scrapeNesine } from '@/lib/scraper/nesine'

export async function GET(request: Request) {
  try {
    const client = new NovadaClient()
    const result = await scrapeNesine(client)
    return NextResponse.json(result)
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 })
  }
}
