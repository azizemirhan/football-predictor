'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

// Match data type
interface Match {
    id: string
    homeTeam: string
    awayTeam: string
    date: string
    time: string
    venue: string
    status: 'scheduled' | 'live' | 'finished'
    homeScore?: number
    awayScore?: number
    league: string
    prediction?: {
        homeWin: number
        draw: number
        awayWin: number
    }
}

// Mock data
const mockMatches: Match[] = [
    {
        id: '1',
        homeTeam: 'Liverpool',
        awayTeam: 'Arsenal',
        date: '2026-01-05',
        time: '17:30',
        venue: 'Anfield',
        status: 'scheduled',
        league: 'Premier League',
        prediction: { homeWin: 0.45, draw: 0.28, awayWin: 0.27 }
    },
    {
        id: '2',
        homeTeam: 'Manchester City',
        awayTeam: 'Chelsea',
        date: '2026-01-05',
        time: '15:00',
        venue: 'Etihad Stadium',
        status: 'scheduled',
        league: 'Premier League',
        prediction: { homeWin: 0.58, draw: 0.24, awayWin: 0.18 }
    },
    {
        id: '3',
        homeTeam: 'Tottenham',
        awayTeam: 'Newcastle',
        date: '2026-01-04',
        time: '20:00',
        venue: 'Tottenham Hotspur Stadium',
        status: 'live',
        homeScore: 1,
        awayScore: 1,
        league: 'Premier League',
        prediction: { homeWin: 0.42, draw: 0.30, awayWin: 0.28 }
    },
    {
        id: '4',
        homeTeam: 'Manchester United',
        awayTeam: 'Aston Villa',
        date: '2026-01-04',
        time: '17:30',
        venue: 'Old Trafford',
        status: 'finished',
        homeScore: 2,
        awayScore: 1,
        league: 'Premier League',
        prediction: { homeWin: 0.48, draw: 0.27, awayWin: 0.25 }
    },
    {
        id: '5',
        homeTeam: 'Brighton',
        awayTeam: 'Wolves',
        date: '2026-01-06',
        time: '15:00',
        venue: 'Amex Stadium',
        status: 'scheduled',
        league: 'Premier League',
        prediction: { homeWin: 0.52, draw: 0.26, awayWin: 0.22 }
    }
]

function MatchCard({ match }: { match: Match }) {
    const statusColors = {
        scheduled: 'bg-blue-500/20 text-blue-400',
        live: 'bg-red-500/20 text-red-400',
        finished: 'bg-gray-500/20 text-gray-400'
    }

    const statusLabels = {
        scheduled: 'Upcoming',
        live: '● LIVE',
        finished: 'FT'
    }

    return (
        <Card className="bg-card/50 border-border/50 hover:border-primary/50 transition-all">
            <CardContent className="p-4">
                {/* Header */}
                <div className="flex justify-between items-center mb-4">
                    <span className="text-xs text-muted-foreground">{match.league}</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${statusColors[match.status]}`}>
                        {statusLabels[match.status]}
                    </span>
                </div>

                {/* Teams & Score */}
                <div className="flex items-center justify-between mb-4">
                    <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                            <span className="font-semibold">{match.homeTeam}</span>
                            {match.status !== 'scheduled' && (
                                <span className="text-2xl font-bold">{match.homeScore}</span>
                            )}
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="font-semibold">{match.awayTeam}</span>
                            {match.status !== 'scheduled' && (
                                <span className="text-2xl font-bold">{match.awayScore}</span>
                            )}
                        </div>
                    </div>
                </div>

                {/* Match Info */}
                <div className="flex items-center gap-4 text-xs text-muted-foreground mb-4">
                    <span>📅 {match.date}</span>
                    <span>⏰ {match.time}</span>
                    <span>📍 {match.venue}</span>
                </div>

                {/* Prediction Bar */}
                {match.prediction && (
                    <div className="space-y-2">
                        <div className="flex justify-between text-xs text-muted-foreground">
                            <span>Home {(match.prediction.homeWin * 100).toFixed(0)}%</span>
                            <span>Draw {(match.prediction.draw * 100).toFixed(0)}%</span>
                            <span>Away {(match.prediction.awayWin * 100).toFixed(0)}%</span>
                        </div>
                        <div className="flex h-2 rounded-full overflow-hidden">
                            <div
                                className="bg-green-500"
                                style={{ width: `${match.prediction.homeWin * 100}%` }}
                            />
                            <div
                                className="bg-yellow-500"
                                style={{ width: `${match.prediction.draw * 100}%` }}
                            />
                            <div
                                className="bg-red-500"
                                style={{ width: `${match.prediction.awayWin * 100}%` }}
                            />
                        </div>
                    </div>
                )}

                {/* Actions */}
                <div className="flex gap-2 mt-4">
                    <Button size="sm" variant="outline" className="flex-1">
                        Details
                    </Button>
                    <Button size="sm" className="flex-1 bg-primary">
                        Predict
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}

export default function MatchesPage() {
    const [filter, setFilter] = useState<'all' | 'live' | 'upcoming' | 'finished'>('all')

    const filteredMatches = mockMatches.filter(match => {
        if (filter === 'all') return true
        if (filter === 'live') return match.status === 'live'
        if (filter === 'upcoming') return match.status === 'scheduled'
        if (filter === 'finished') return match.status === 'finished'
        return true
    })

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Matches</h1>
                    <p className="text-muted-foreground">Premier League fixtures and results</p>
                </div>
            </div>

            {/* Filters */}
            <div className="flex gap-2">
                {(['all', 'live', 'upcoming', 'finished'] as const).map((f) => (
                    <Button
                        key={f}
                        variant={filter === f ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setFilter(f)}
                        className={filter === f ? 'bg-primary' : ''}
                    >
                        {f === 'all' ? 'All Matches' : f === 'live' ? '● Live' : f.charAt(0).toUpperCase() + f.slice(1)}
                    </Button>
                ))}
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold">{mockMatches.length}</div>
                        <div className="text-sm text-muted-foreground">Total Matches</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-red-400">
                            {mockMatches.filter(m => m.status === 'live').length}
                        </div>
                        <div className="text-sm text-muted-foreground">Live Now</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-blue-400">
                            {mockMatches.filter(m => m.status === 'scheduled').length}
                        </div>
                        <div className="text-sm text-muted-foreground">Upcoming</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-gray-400">
                            {mockMatches.filter(m => m.status === 'finished').length}
                        </div>
                        <div className="text-sm text-muted-foreground">Finished</div>
                    </CardContent>
                </Card>
            </div>

            {/* Matches Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredMatches.map((match) => (
                    <MatchCard key={match.id} match={match} />
                ))}
            </div>

            {filteredMatches.length === 0 && (
                <div className="text-center py-12 text-muted-foreground">
                    No matches found for the selected filter.
                </div>
            )}
        </div>
    )
}
