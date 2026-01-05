'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'

interface ValueBet {
    id: number
    matchId: number
    homeTeam: string
    awayTeam: string
    date: string
    selection: 'home' | 'draw' | 'away'
    odds: number
    predictedProb: number
    edge: number
    kellyStake: number
    bookmaker: string
    result: 'pending' | 'won' | 'lost' | 'void'
}

interface OddsData {
    id: number
    matchId: number
    bookmaker: string
    homeOdds: number
    drawOdds: number
    awayOdds: number
    homeTeam: string
    awayTeam: string
}

function ValueBetCard({ bet }: { bet: ValueBet }) {
    const statusColors = {
        pending: 'bg-blue-500/20 text-blue-400',
        won: 'bg-green-500/20 text-green-400',
        lost: 'bg-red-500/20 text-red-400',
        void: 'bg-gray-500/20 text-gray-400'
    }

    const selectionLabels = {
        home: `${bet.homeTeam} Kazanır`,
        draw: 'Beraberlik',
        away: `${bet.awayTeam} Kazanır`
    }

    const edgeColor = bet.edge >= 0.08 ? 'text-green-400' : bet.edge >= 0.05 ? 'text-yellow-400' : 'text-orange-400'

    return (
        <Card className="bg-card/50 border-border/50 hover:border-primary/50 transition-all">
            <CardContent className="p-4">
                {/* Header */}
                <div className="flex justify-between items-center mb-3">
                    <div className="flex items-center gap-2">
                        <span className="text-xs px-2 py-1 rounded bg-primary/20 text-primary">
                            {bet.bookmaker}
                        </span>
                        <span className={`text-xs px-2 py-1 rounded-full ${statusColors[bet.result]}`}>
                            {bet.result === 'pending' ? 'Aktif' : bet.result === 'won' ? 'Kazandı' : bet.result === 'lost' ? 'Kaybetti' : 'İptal'}
                        </span>
                    </div>
                    <span className="text-xs text-muted-foreground">{bet.date}</span>
                </div>

                {/* Match */}
                <div className="mb-3">
                    <div className="font-semibold">{bet.homeTeam} vs {bet.awayTeam}</div>
                    <div className="text-lg font-bold text-primary mt-1">
                        {selectionLabels[bet.selection]}
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                        <div className="text-xs text-muted-foreground">Oran</div>
                        <div className="text-xl font-bold">{bet.odds.toFixed(2)}</div>
                    </div>
                    <div>
                        <div className="text-xs text-muted-foreground">Edge</div>
                        <div className={`text-xl font-bold ${edgeColor}`}>
                            +{(bet.edge * 100).toFixed(1)}%
                        </div>
                    </div>
                    <div>
                        <div className="text-xs text-muted-foreground">Tahmin Olasılık</div>
                        <div className="text-lg font-semibold">{(bet.predictedProb * 100).toFixed(1)}%</div>
                    </div>
                    <div>
                        <div className="text-xs text-muted-foreground">Kelly Stake</div>
                        <div className="text-lg font-semibold">{(bet.kellyStake * 100).toFixed(1)}%</div>
                    </div>
                </div>

                {/* Edge Progress Bar */}
                <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                        <span className="text-muted-foreground">Edge Seviyesi</span>
                        <span className={edgeColor}>{(bet.edge * 100).toFixed(1)}%</span>
                    </div>
                    <Progress value={Math.min(bet.edge * 1000, 100)} className="h-2" />
                </div>

                {/* Action */}
                {bet.result === 'pending' && (
                    <Button className="w-full mt-4 bg-gradient-to-r from-green-600 to-emerald-600">
                        ⚡ Bahis Yap
                    </Button>
                )}
            </CardContent>
        </Card>
    )
}

function OddsCard({ odds }: { odds: OddsData }) {
    return (
        <Card className="bg-card/50 border-border/50">
            <CardContent className="p-4">
                <div className="flex justify-between items-center mb-2">
                    <span className="font-medium text-sm">{odds.homeTeam} vs {odds.awayTeam}</span>
                    <span className="text-xs px-2 py-1 rounded bg-blue-500/20 text-blue-400">
                        {odds.bookmaker}
                    </span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="bg-green-500/10 rounded p-2">
                        <div className="text-xs text-muted-foreground">Ev</div>
                        <div className="font-bold text-green-400">{odds.homeOdds.toFixed(2)}</div>
                    </div>
                    <div className="bg-yellow-500/10 rounded p-2">
                        <div className="text-xs text-muted-foreground">X</div>
                        <div className="font-bold text-yellow-400">{odds.drawOdds.toFixed(2)}</div>
                    </div>
                    <div className="bg-red-500/10 rounded p-2">
                        <div className="text-xs text-muted-foreground">Depl</div>
                        <div className="font-bold text-red-400">{odds.awayOdds.toFixed(2)}</div>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}

export default function ValueBetsPage() {
    const [valueBets, setValueBets] = useState<ValueBet[]>([])
    const [odds, setOdds] = useState<OddsData[]>([])
    const [loading, setLoading] = useState(true)
    const [syncing, setSyncing] = useState(false)
    const [filter, setFilter] = useState<'all' | 'pending' | 'won' | 'lost'>('all')

    const fetchData = async () => {
        try {
            setLoading(true)
            const response = await fetch('/api/odds')
            const data = await response.json()
            
            if (data.valueBets) {
                const formattedBets = data.valueBets.map((vb: any) => ({
                    id: vb.id,
                    matchId: vb.match_id,
                    homeTeam: 'Home Team', // Would need match join
                    awayTeam: 'Away Team',
                    date: new Date(vb.created_at).toISOString().split('T')[0],
                    selection: vb.selection,
                    odds: vb.market_odds,
                    predictedProb: vb.predicted_prob,
                    edge: vb.edge,
                    kellyStake: vb.kelly_stake,
                    bookmaker: 'Nesine',
                    result: vb.result
                }))
                setValueBets(formattedBets)
            }
            
            if (data.odds) {
                const formattedOdds = data.odds.slice(0, 10).map((o: any) => ({
                    id: o.id,
                    matchId: o.match_id,
                    bookmaker: o.bookmaker,
                    homeOdds: o.home_odds,
                    drawOdds: o.draw_odds,
                    awayOdds: o.away_odds,
                    homeTeam: o.match?.home_team?.short_name || 'Home',
                    awayTeam: o.match?.away_team?.short_name || 'Away'
                }))
                setOdds(formattedOdds)
            }
        } catch (error) {
            console.error('Failed to fetch odds:', error)
        } finally {
            setLoading(false)
        }
    }

    const syncOdds = async () => {
        setSyncing(true)
        try {
            await fetch('/api/odds', { method: 'POST', body: JSON.stringify({}) })
            await fetchData()
        } finally {
            setSyncing(false)
        }
    }

    useEffect(() => {
        fetchData()
    }, [])

    const filteredBets = valueBets.filter(bet => {
        if (filter === 'all') return true
        return bet.result === filter
    })

    const stats = {
        totalBets: valueBets.length,
        pending: valueBets.filter(b => b.result === 'pending').length,
        won: valueBets.filter(b => b.result === 'won').length,
        lost: valueBets.filter(b => b.result === 'lost').length,
        avgEdge: valueBets.length > 0 
            ? valueBets.reduce((sum, b) => sum + b.edge, 0) / valueBets.length 
            : 0
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Value Bets</h1>
                    <p className="text-muted-foreground">AI tahminlerine dayalı değerli bahis fırsatları</p>
                </div>
                <Button 
                    onClick={syncOdds} 
                    disabled={syncing}
                    className="gap-2"
                >
                    {syncing ? '⏳ Senkronize...' : '🔄 Oranları Güncelle'}
                </Button>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold">{stats.totalBets}</div>
                        <div className="text-sm text-muted-foreground">Toplam Bahis</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-blue-400">{stats.pending}</div>
                        <div className="text-sm text-muted-foreground">Aktif</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-green-400">{stats.won}</div>
                        <div className="text-sm text-muted-foreground">Kazanan</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-red-400">{stats.lost}</div>
                        <div className="text-sm text-muted-foreground">Kaybeden</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-primary">
                            +{(stats.avgEdge * 100).toFixed(1)}%
                        </div>
                        <div className="text-sm text-muted-foreground">Ort. Edge</div>
                    </CardContent>
                </Card>
            </div>

            {/* Filters */}
            <div className="flex gap-2">
                {(['all', 'pending', 'won', 'lost'] as const).map((f) => (
                    <Button
                        key={f}
                        variant={filter === f ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setFilter(f)}
                    >
                        {f === 'all' ? 'Tümü' : f === 'pending' ? 'Aktif' : f === 'won' ? 'Kazanan' : 'Kaybeden'}
                    </Button>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Value Bets */}
                <div className="lg:col-span-2 space-y-4">
                    <h2 className="text-xl font-bold">🎯 Değerli Bahisler</h2>
                    {filteredBets.length === 0 ? (
                        <Card className="bg-card/50">
                            <CardContent className="p-8 text-center text-muted-foreground">
                                <p>Henüz value bet bulunamadı.</p>
                                <p className="text-sm mt-2">Oranları güncelleyerek yeni fırsatları keşfedin.</p>
                            </CardContent>
                        </Card>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {filteredBets.map((bet) => (
                                <ValueBetCard key={bet.id} bet={bet} />
                            ))}
                        </div>
                    )}
                </div>

                {/* Latest Odds */}
                <div className="space-y-4">
                    <h2 className="text-xl font-bold">📊 Son Oranlar</h2>
                    <div className="space-y-3">
                        {odds.map((o) => (
                            <OddsCard key={o.id} odds={o} />
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}
