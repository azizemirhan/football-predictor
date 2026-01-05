import { NextResponse } from 'next/server'

export async function POST(request: Request) {
    const body = await request.json()
    
    console.log('Webhook received:', body)
    
    // TODO: Process webhooks from external services
    // e.g., Telegram bot, Discord, Stripe, etc.
    
    return NextResponse.json({
        message: 'Webhook received',
        received: true
    })
}

export async function GET() {
    return NextResponse.json({
        message: 'Webhook endpoint active',
        status: 'ok'
    })
}
