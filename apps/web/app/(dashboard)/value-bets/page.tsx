'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'

interface ValueBet {
    id: string
    homeTeam: string
    awayTeam: string
    date: string
    selection: string
    selectionType: 'home' | 'draw' | 'away' | 'over' | 'under'
    odds: number
    predictedProb: number
    impliedProb: number
    edge: number
    kellyStake: number
    confidence: number
    bookmaker: string
    status: 'active' | 'won' | 'lost' | 'void'
}

const mockValueBets: ValueBet[] = [
    {
        id: '1',
        homeTeam: 'Liverpool',
        awayTeam: 'Arsenal',
        date: '2026-01-05',
        selection: 'Liverpool Win',
        selectionType: 'home',
        odds: 2.40,
        predictedProb: 0.45,
        impliedProb: 0.417,
        edge: 0.08,
        kellyStake: 0.034,
        confidence: 0.72,
        bookmaker: 'Pinnacle',
        status: 'active'
    },
    {
        id: '2',
        homeTeam: 'Manchester City',
        awayTeam: 'Chelsea',
        date: '2026-01-05',
        selection: 'Over 2.5',
        selectionType: 'over',
        odds: 1.85,
        predictedProb: 0.62,
        impliedProb: 0.54,
        edge: 0.08,
        kellyStake: 0.052,
        confidence: 0.78,
        bookmaker: 'bet365',
        status: 'active'
    },
    {
        id: '3',
        homeTeam: 'Brighton',
        awayTeam: 'Wolves',
        date: '2026-01-06',
        selection: 'Brighton Win',
        selectionType: 'home',
        odds: 1.95,
        predictedProb: 0.58,
        impliedProb: 0.513,
        edge: 0.067,
        kellyStake: 0.041,
        confidence: 0.65,
        bookmaker: 'Pinnacle',
        status: 'active'
    },
    {
        id: '4',
        homeTeam: 'Tottenham',
        awayTeam: 'Newcastle',
        date: '2026-01-04',
        selection: 'Draw',
        selectionType: 'draw',
        odds: 3.60,
        predictedProb: 0.32,
        impliedProb: 0.278,
        edge: 0.042,
        kellyStake: 0.018,
        confidence: 0.58,
        bookmaker: 'Betfair',
        status: 'won'
    },
    {
        id: '5',
        homeTeam: 'Everton',
        awayTeam: 'West Ham',
        date: '2026-01-03',
        selection: 'Under 2.5',
        selectionType: 'under',
        odds: 2.10,
        predictedProb: 0.52,
        impliedProb: 0.476,
        edge: 0.044,
        kellyStake: 0.022,
        confidence: 0.61,
        bookmaker: 'bet365',
        status: 'lost'
    }
]

function ValueBetCard({ bet }: { bet: ValueBet }) {
    const edgeColor = bet.edge >= 0.1 ? 'text-green-400' : bet.edge >= 0.05 ? 'text-yellow-400' : 'text-orange-400'
    const statusColors = {
        active: 'bg-blue-500/20 text-blue-400',
        won: 'bg-green-500/20 text-green-400',
        lost: 'bg-red-500/20 text-red-400',
        void: 'bg-gray-500/20 text-gray-400'
    }

    return (
        <Card className="bg-card/50 border-border/50 hover:border-primary/50 transition-all">
            <CardContent className="p-4">
                {/* Header */}
                <div className="flex justify-between items-start mb-3">
                    <div>
                        <div className="font-semibold">{bet.homeTeam} vs {bet.awayTeam}</div>
                        <div className="text-xs text-muted-foreground">📅 {bet.date} | {bet.bookmaker}</div>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${statusColors[bet.status]}`}>
                        {bet.status.toUpperCase()}
                    </span>
                </div>

                {/* Selection */}
                <div className="bg-primary/10 rounded-lg p-3 mb-3">
                    <div className="flex justify-between items-center">
                        <div>
                            <div className="text-sm text-muted-foreground">Selection</div>
                            <div className="text-lg font-bold">{bet.selection}</div>
                        </div>
                        <div className="text-right">
                            <div className="text-sm text-muted-foreground">Odds</div>
                            <div className="text-2xl font-bold text-primary">{bet.odds.toFixed(2)}</div>
                        </div>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-3 gap-2 mb-3">
                    <div className="text-center p-2 bg-muted/30 rounded">
                        <div className="text-lg font-bold">{(bet.predictedProb * 100).toFixed(0)}%</div>
                        <div className="text-xs text-muted-foreground">Model</div>
                    </div>
                    <div className="text-center p-2 bg-muted/30 rounded">
                        <div className="text-lg font-bold">{(bet.impliedProb * 100).toFixed(0)}%</div>
                        <div className="text-xs text-muted-foreground">Implied</div>
                    </div>
                    <div className="text-center p-2 bg-muted/30 rounded">
                        <div className={`text-lg font-bold ${edgeColor}`}>+{(bet.edge * 100).toFixed(1)}%</div>
                        <div className="text-xs text-muted-foreground">Edge</div>
                    </div>
                </div>

                {/* Kelly & Confidence */}
                <div className="flex justify-between items-center text-sm">
                    <div>
                        <span className="text-muted-foreground">Kelly Stake: </span>
                        <span className="font-medium">{(bet.kellyStake * 100).toFixed(1)}%</span>
                    </div>
                    <div>
                        <span className="text-muted-foreground">Confidence: </span>
                        <span className="font-medium">{(bet.confidence * 100).toFixed(0)}%</span>
                    </div>
                </div>

                {/* Edge Bar */}
                <div className="mt-3">
                    <div className="flex justify-between text-xs text-muted-foreground mb-1">
                        <span>Value Edge</span>
                        <span>{(bet.edge * 100).toFixed(1)}%</span>
                    </div>
                    <Progress value={bet.edge * 1000} className="h-2" />
                </div>
            </CardContent>
        </Card>
    )
}

export default function ValueBetsPage() {
    const [filter, setFilter] = useState<'all' | 'active' | 'won' | 'lost'>('all')

    const filteredBets = mockValueBets.filter(bet => {
        if (filter === 'all') return true
        return bet.status === filter
    })

    const activeBets = mockValueBets.filter(b => b.status === 'active')
    const wonBets = mockValueBets.filter(b => b.status === 'won')
    const lostBets = mockValueBets.filter(b => b.status === 'lost')
    const totalEdge = activeBets.reduce((sum, b) => sum + b.edge, 0) / (activeBets.length || 1)

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Value Bets</h1>
                    <p className="text-muted-foreground">High-edge betting opportunities detected by AI</p>
                </div>
                <Button className="bg-primary">
                    Scan Now
                </Button>
            </div>

            {/* Filters */}
            <div className="flex gap-2">
                {(['all', 'active', 'won', 'lost'] as const).map((f) => (
                    <Button
                        key={f}
                        variant={filter === f ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setFilter(f)}
                    >
                        {f.charAt(0).toUpperCase() + f.slice(1)}
                    </Button>
                ))}
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-blue-400">{activeBets.length}</div>
                        <div className="text-sm text-muted-foreground">Active Bets</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-green-400">+{(totalEdge * 100).toFixed(1)}%</div>
                        <div className="text-sm text-muted-foreground">Avg Edge</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-green-400">{wonBets.length}</div>
                        <div className="text-sm text-muted-foreground">Won</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-red-400">{lostBets.length}</div>
                        <div className="text-sm text-muted-foreground">Lost</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-primary">
                            {wonBets.length + lostBets.length > 0
                                ? ((wonBets.length / (wonBets.length + lostBets.length)) * 100).toFixed(0)
                                : 0}%
                        </div>
                        <div className="text-sm text-muted-foreground">Win Rate</div>
                    </CardContent>
                </Card>
            </div>

            {/* ROI Summary */}
            <Card className="bg-gradient-to-r from-green-500/10 to-primary/10">
                <CardContent className="p-6">
                    <div className="flex justify-between items-center">
                        <div>
                            <div className="text-sm text-muted-foreground">Monthly ROI</div>
                            <div className="text-4xl font-bold text-green-400">+12.5%</div>
                        </div>
                        <div className="text-right">
                            <div className="text-sm text-muted-foreground">Total Profit</div>
                            <div className="text-4xl font-bold">£1,250</div>
                        </div>
                        <div className="text-right">
                            <div className="text-sm text-muted-foreground">Bets Placed</div>
                            <div className="text-4xl font-bold">48</div>
                        </div>
                        <div className="text-right">
                            <div className="text-sm text-muted-foreground">Avg Stake</div>
                            <div className="text-4xl font-bold">3.2%</div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Value Bets Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredBets.map((bet) => (
                    <ValueBetCard key={bet.id} bet={bet} />
                ))}
            </div>

            {filteredBets.length === 0 && (
                <div className="text-center py-12 text-muted-foreground">
                    No value bets found for the selected filter.
                </div>
            )}
        </div>
    )
}
