import { NextResponse } from 'next/server'

const mockPredictions = [
    {
        id: '1',
        matchId: '1',
        homeTeam: 'Liverpool',
        awayTeam: 'Arsenal',
        prediction: {
            home: 0.45,
            draw: 0.28,
            away: 0.27
        },
        expectedScore: '2-1',
        confidence: 0.72
    },
    {
        id: '2',
        matchId: '2',
        homeTeam: 'Manchester City',
        awayTeam: 'Chelsea',
        prediction: {
            home: 0.58,
            draw: 0.24,
            away: 0.18
        },
        expectedScore: '3-1',
        confidence: 0.81
    }
]

export async function GET() {
    // TODO: Fetch from AI engine
    return NextResponse.json({
        predictions: mockPredictions,
        total: mockPredictions.length
    })
}

export async function POST(request: Request) {
    const body = await request.json()
    
    // TODO: Generate prediction via AI engine
    return NextResponse.json({
        message: 'Prediction generated',
        prediction: {
            id: 'new',
            matchId: body.matchId,
            prediction: { home: 0.5, draw: 0.25, away: 0.25 },
            confidence: 0.65
        }
    })
}
