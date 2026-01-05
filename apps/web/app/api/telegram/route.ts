import { NextResponse } from 'next/server'
import { sendTelegramMessage } from '@/lib/telegram'

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { message } = body
    
    if (!message) {
      return NextResponse.json({ error: 'Message required' }, { status: 400 })
    }
    
    const success = await sendTelegramMessage(message)
    
    if (success) {
      return NextResponse.json({ success: true, message: 'Sent' })
    } else {
      return NextResponse.json({ 
        success: false, 
        error: 'Failed (Check server logs - Token/ChatID configured?)' 
      }, { status: 500 })
    }
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 })
  }
}
