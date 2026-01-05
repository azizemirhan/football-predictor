import { NextResponse } from 'next/server'

export async function GET() {
    return NextResponse.json({
        message: 'Auth endpoint',
        status: 'ok'
    })
}

export async function POST(request: Request) {
    const body = await request.json()
    
    // TODO: Implement actual authentication with Supabase
    return NextResponse.json({
        message: 'Login successful',
        user: {
            id: '1',
            email: body.email,
            name: 'Demo User'
        }
    })
}
