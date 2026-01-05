'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import Image from 'next/image'
import Link from 'next/link'

// Match data type
interface Match {
    id: number
    externalId: string
    homeTeam: string
    homeTeamShort: string
    homeTeamLogo?: string
    awayTeam: string
    awayTeamShort: string
    awayTeamLogo?: string
    date: string
    time: string
    venue: string
    status: 'scheduled' | 'live' | 'finished' | 'postponed' | 'cancelled'
    homeScore?: number | null
    awayScore?: number | null
    minute?: number | null
    league: string
    prediction?: {
        homeWin: number
        draw: number
        awayWin: number
    }
    // Single odds for backward compat (first bookmaker)
    odds?: {
        home: number
        draw: number
        away: number
        bookmaker: string
    } | null
    // All bookmakers' odds for tabbed display
    allOdds?: {
        bookmaker: string
        home: number
        draw: number
        away: number
    }[]
}

interface MatchesResponse {
    matches: Match[]
    total: number
    stats: {
        live: number
        upcoming: number
        finished: number
    }
    error?: string
}

// Tabbed Odds Box Component
function OddsTabsBox({ allOdds }: { allOdds: { bookmaker: string; home: number; draw: number; away: number }[] }) {
    const [activeTab, setActiveTab] = useState(0);
    
    // Define bookmaker order: Nesine first, then Iddaa, then others
    const bookmakers = ['Nesine', 'Iddaa'];
    const sortedOdds = allOdds.sort((a, b) => {
        const aIdx = bookmakers.indexOf(a.bookmaker);
        const bIdx = bookmakers.indexOf(b.bookmaker);
        return (aIdx === -1 ? 999 : aIdx) - (bIdx === -1 ? 999 : bIdx);
    });
    
    if (sortedOdds.length === 0) return null;
    
    const currentOdds = sortedOdds[activeTab] || sortedOdds[0];
    
    return (
        <div className="mt-3 p-3 bg-gradient-to-r from-emerald-500/10 to-blue-500/10 rounded-lg border border-emerald-500/20">
            {/* Bookmaker Tabs */}
            <div className="flex justify-between items-center mb-2">
                <div className="flex gap-1">
                    {sortedOdds.map((odds, idx) => (
                        <button
                            key={odds.bookmaker}
                            onClick={() => setActiveTab(idx)}
                            className={`text-[10px] px-2 py-0.5 rounded-full transition-colors ${
                                activeTab === idx
                                    ? 'bg-emerald-500/30 text-emerald-300 border border-emerald-500/50'
                                    : 'bg-background/30 text-muted-foreground hover:bg-emerald-500/10'
                            }`}
                        >
                            {odds.bookmaker}
                        </button>
                    ))}
                </div>
                <span className="text-xs text-muted-foreground font-medium">Oranlar</span>
            </div>
            
            {/* Odds Grid */}
            <div className="grid grid-cols-3 gap-2">
                <div className="text-center p-2 bg-background/50 rounded-md hover:bg-green-500/20 transition-colors cursor-pointer border border-transparent hover:border-green-500/50">
                    <div className="text-lg font-bold text-green-400">{currentOdds.home?.toFixed(2) || '-'}</div>
                    <div className="text-[10px] text-muted-foreground">MS1</div>
                </div>
                <div className="text-center p-2 bg-background/50 rounded-md hover:bg-yellow-500/20 transition-colors cursor-pointer border border-transparent hover:border-yellow-500/50">
                    <div className="text-lg font-bold text-yellow-400">{currentOdds.draw?.toFixed(2) || '-'}</div>
                    <div className="text-[10px] text-muted-foreground">X</div>
                </div>
                <div className="text-center p-2 bg-background/50 rounded-md hover:bg-red-500/20 transition-colors cursor-pointer border border-transparent hover:border-red-500/50">
                    <div className="text-lg font-bold text-red-400">{currentOdds.away?.toFixed(2) || '-'}</div>
                    <div className="text-[10px] text-muted-foreground">MS2</div>
                </div>
            </div>
        </div>
    );
}

function MatchCard({ match }: { match: Match }) {
    const statusColors = {
        scheduled: 'bg-blue-500/20 text-blue-400',
        live: 'bg-red-500/20 text-red-400 animate-pulse',
        finished: 'bg-gray-500/20 text-gray-400',
        postponed: 'bg-yellow-500/20 text-yellow-400',
        cancelled: 'bg-red-800/20 text-red-600'
    }

    const statusLabels = {
        scheduled: 'Upcoming',
        live: '● LIVE',
        finished: 'FT',
        postponed: 'Postponed',
        cancelled: 'Cancelled'
    }

    return (
        <Card className="bg-card/50 border-border/50 hover:border-primary/50 transition-all hover:shadow-lg hover:shadow-primary/10">
            <CardContent className="p-4">
                {/* Header */}
                <div className="flex justify-between items-center mb-4">
                    <span className="text-xs text-muted-foreground">{match.league}</span>
                    <div className="flex items-center gap-2">
                        {match.status === 'live' && match.minute && (
                            <span className="text-xs font-mono font-bold text-red-400 animate-pulse">
                                {match.minute}'
                            </span>
                        )}
                        <span className={`text-xs px-2 py-1 rounded-full ${statusColors[match.status]}`}>
                            {statusLabels[match.status]}
                        </span>
                    </div>
                </div>

                {/* Teams & Score */}
                <div className="space-y-3 mb-4">
                    {/* Home Team */}
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            {match.homeTeamLogo && (
                                <Image 
                                    src={match.homeTeamLogo} 
                                    alt={match.homeTeam}
                                    width={28}
                                    height={28}
                                    className="rounded"
                                />
                            )}
                            <span className="font-semibold">{match.homeTeam}</span>
                        </div>
                        {match.status !== 'scheduled' && match.homeScore !== null && (
                            <span className="text-2xl font-bold">{match.homeScore}</span>
                        )}
                    </div>
                    
                    {/* Away Team */}
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            {match.awayTeamLogo && (
                                <Image 
                                    src={match.awayTeamLogo} 
                                    alt={match.awayTeam}
                                    width={28}
                                    height={28}
                                    className="rounded"
                                />
                            )}
                            <span className="font-semibold">{match.awayTeam}</span>
                        </div>
                        {match.status !== 'scheduled' && match.awayScore !== null && (
                            <span className="text-2xl font-bold">{match.awayScore}</span>
                        )}
                    </div>
                </div>

                {/* Match Info */}
                <div className="flex items-center gap-4 text-xs text-muted-foreground mb-4">
                    <span>📅 {match.date}</span>
                    <span>⏰ {match.time}</span>
                </div>

                {/* Prediction Bar */}
                {match.prediction && match.status === 'scheduled' && (
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

                {/* Tabbed Odds Box */}
                {match.status === 'scheduled' && (match.allOdds?.length || match.odds) && (
                    <OddsTabsBox 
                        allOdds={match.allOdds || (match.odds ? [{
                            bookmaker: match.odds.bookmaker,
                            home: match.odds.home,
                            draw: match.odds.draw,
                            away: match.odds.away
                        }] : [])}
                    />
                )}

                {/* Actions */}
                <div className="flex gap-2 mt-4">
                    <Link href={`/matches/${match.externalId}`} className="flex-1">
                        <Button size="sm" variant="outline" className="w-full">
                            Details
                        </Button>
                    </Link>
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
    const [matches, setMatches] = useState<Match[]>([])
    const [stats, setStats] = useState({ live: 0, upcoming: 0, finished: 0 })
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        async function fetchMatches() {
            try {
                setLoading(true)
                const response = await fetch('/api/matches')
                const data: MatchesResponse = await response.json()
                
                if (data.error) {
                    setError(data.error as string)
                } else {
                    setMatches(data.matches)
                    setStats(data.stats)
                }
            } catch (err) {
                setError('Failed to fetch matches')
                console.error(err)
            } finally {
                setLoading(false)
            }
        }

        fetchMatches()
    }, [])

    const filteredMatches = matches.filter(match => {
        if (filter === 'all') return true
        if (filter === 'live') return match.status === 'live'
        if (filter === 'upcoming') return match.status === 'scheduled'
        if (filter === 'finished') return match.status === 'finished'
        return true
    })

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="text-center py-12">
                <p className="text-red-500 mb-4">{error}</p>
                <Button onClick={() => window.location.reload()}>Retry</Button>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Matches</h1>
                    <p className="text-muted-foreground">Premier League fixtures and results</p>
                </div>
                <Button 
                    variant="outline" 
                    onClick={() => window.location.reload()}
                    className="gap-2"
                >
                    🔄 Refresh
                </Button>
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
                        <div className="text-2xl font-bold">{matches.length}</div>
                        <div className="text-sm text-muted-foreground">Total Matches</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-red-400">
                            {stats.live}
                        </div>
                        <div className="text-sm text-muted-foreground">Live Now</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-blue-400">
                            {stats.upcoming}
                        </div>
                        <div className="text-sm text-muted-foreground">Upcoming</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-gray-400">
                            {stats.finished}
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
