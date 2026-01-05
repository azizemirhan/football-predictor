'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import Image from 'next/image'
import Link from 'next/link'
import {
    TrendingUp,
    Target,
    Zap,
    Calendar,
    ChevronRight,
    Trophy,
    BarChart3,
    DollarSign
} from "lucide-react"

interface DashboardData {
    stats: {
        totalMatches: number
        upcomingMatches: number
        liveMatches: number
        totalTeams: number
        totalOdds: number
        activeValueBets: number
        avgEdge: number
    }
    upcomingMatches: {
        id: number
        homeTeam: string
        homeTeamFull: string
        homeTeamLogo?: string
        awayTeam: string
        awayTeamFull: string
        awayTeamLogo?: string
        date: string
        time: string
        prediction: { home: number; draw: number; away: number }
        confidence: 'high' | 'medium' | 'low'
    }[]
    topValueBets: {
        id: number
        match: string
        selection: string
        odds: number
        edge: number
        kellyStake: number
    }[]
    lastUpdated: string
}

// Stat Card Component
function StatCard({
    title,
    value,
    subtitle,
    icon: Icon,
    color = 'primary'
}: {
    title: string
    value: string | number
    subtitle?: string
    icon: React.ElementType
    color?: 'primary' | 'green' | 'blue' | 'orange'
}) {
    const colors = {
        primary: 'bg-primary/10 text-primary',
        green: 'bg-green-500/10 text-green-500',
        blue: 'bg-blue-500/10 text-blue-500',
        orange: 'bg-orange-500/10 text-orange-500'
    }

    return (
        <Card className="bg-card/50 border-border/50">
            <CardContent className="p-5">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm text-muted-foreground">{title}</p>
                        <p className="text-2xl font-bold mt-1">{value}</p>
                        {subtitle && (
                            <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
                        )}
                    </div>
                    <div className={`h-12 w-12 rounded-full ${colors[color]} flex items-center justify-center`}>
                        <Icon className="h-6 w-6" />
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}

// Upcoming Match Component
function UpcomingMatch({ match }: { match: DashboardData['upcomingMatches'][0] }) {
    const confidenceColors = {
        high: 'bg-green-500/20 text-green-400',
        medium: 'bg-yellow-500/20 text-yellow-400',
        low: 'bg-red-500/20 text-red-400'
    }

    return (
        <Card className="bg-card/50 border-border/50 hover:border-primary/50 transition-all">
            <CardContent className="p-4">
                <div className="flex items-center justify-between mb-3">
                    <span className="text-xs text-muted-foreground">{match.date} - {match.time}</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${confidenceColors[match.confidence]}`}>
                        {match.confidence === 'high' ? 'Yüksek Güven' : 'Orta Güven'}
                    </span>
                </div>

                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        {match.homeTeamLogo ? (
                            <Image src={match.homeTeamLogo} alt={match.homeTeam} width={32} height={32} className="rounded" />
                        ) : (
                            <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center">
                                <Trophy className="h-4 w-4" />
                            </div>
                        )}
                        <span className="font-semibold">{match.homeTeam}</span>
                    </div>
                    <span className="text-muted-foreground text-sm">vs</span>
                    <div className="flex items-center gap-2">
                        <span className="font-semibold">{match.awayTeam}</span>
                        {match.awayTeamLogo ? (
                            <Image src={match.awayTeamLogo} alt={match.awayTeam} width={32} height={32} className="rounded" />
                        ) : (
                            <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center">
                                <Trophy className="h-4 w-4" />
                            </div>
                        )}
                    </div>
                </div>

                {/* Prediction Bars */}
                <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                        <span className="text-green-400">Ev {match.prediction.home}%</span>
                        <span className="text-yellow-400">X {match.prediction.draw}%</span>
                        <span className="text-red-400">Dep {match.prediction.away}%</span>
                    </div>
                    <div className="flex h-2 rounded-full overflow-hidden">
                        <div className="bg-green-500" style={{ width: `${match.prediction.home}%` }} />
                        <div className="bg-yellow-500" style={{ width: `${match.prediction.draw}%` }} />
                        <div className="bg-red-500" style={{ width: `${match.prediction.away}%` }} />
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}

// Value Bet Card
function ValueBetItem({ bet }: { bet: DashboardData['topValueBets'][0] }) {
    const selectionLabels: Record<string, string> = {
        home: 'Ev Sahibi',
        draw: 'Beraberlik',
        away: 'Deplasman'
    }

    return (
        <div className="flex items-center justify-between p-3 bg-card/30 rounded-lg hover:bg-card/50 transition-all">
            <div>
                <div className="font-medium text-sm">{bet.match}</div>
                <div className="text-xs text-primary">{selectionLabels[bet.selection] || bet.selection}</div>
            </div>
            <div className="text-right">
                <div className="font-bold">{bet.odds.toFixed(2)}</div>
                <div className="text-xs text-green-400">+{(bet.edge * 100).toFixed(1)}%</div>
            </div>
        </div>
    )
}

export default function DashboardPage() {
    const [data, setData] = useState<DashboardData | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        async function fetchDashboard() {
            try {
                const response = await fetch('/api/dashboard')
                const result = await response.json()
                setData(result)
            } catch (error) {
                console.error('Failed to fetch dashboard:', error)
            } finally {
                setLoading(false)
            }
        }

        fetchDashboard()
    }, [])

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
            </div>
        )
    }

    if (!data) {
        return (
            <div className="text-center py-12">
                <p className="text-muted-foreground">Veriler yüklenemedi</p>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent">
                        Dashboard
                    </h1>
                    <p className="text-muted-foreground">Premier League AI Tahmin Merkezi</p>
                </div>
                <div className="flex gap-2">
                    <Link href="/matches">
                        <Button variant="outline" className="gap-2">
                            <Calendar className="h-4 w-4" />
                            Maçlar
                        </Button>
                    </Link>
                    <Link href="/value-bets">
                        <Button className="gap-2 bg-gradient-to-r from-green-600 to-emerald-600">
                            <Zap className="h-4 w-4" />
                            Value Bets
                        </Button>
                    </Link>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    title="Toplam Maç"
                    value={data.stats.totalMatches}
                    subtitle={`${data.stats.upcomingMatches} yaklaşan`}
                    icon={Calendar}
                    color="primary"
                />
                <StatCard
                    title="Takımlar"
                    value={data.stats.totalTeams}
                    subtitle="Premier League"
                    icon={Trophy}
                    color="blue"
                />
                <StatCard
                    title="Aktif Value Bets"
                    value={data.stats.activeValueBets}
                    subtitle={`Ort. Edge: +${(data.stats.avgEdge * 100).toFixed(1)}%`}
                    icon={Target}
                    color="green"
                />
                <StatCard
                    title="Bahis Oranları"
                    value={data.stats.totalOdds}
                    subtitle="Nesine / İddaa"
                    icon={BarChart3}
                    color="orange"
                />
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Upcoming Matches */}
                <div className="lg:col-span-2 space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-bold flex items-center gap-2">
                            <Calendar className="h-5 w-5 text-primary" />
                            Yaklaşan Maçlar
                        </h2>
                        <Link href="/matches">
                            <Button variant="ghost" size="sm" className="gap-1">
                                Tümünü Gör <ChevronRight className="h-4 w-4" />
                            </Button>
                        </Link>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {data.upcomingMatches.map((match) => (
                            <UpcomingMatch key={match.id} match={match} />
                        ))}
                    </div>
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    {/* Top Value Bets */}
                    <Card className="bg-card/50 border-border/50">
                        <CardContent className="p-4">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="font-bold flex items-center gap-2">
                                    <Target className="h-4 w-4 text-green-500" />
                                    En İyi Value Bets
                                </h3>
                                <Link href="/value-bets">
                                    <Button variant="ghost" size="sm">
                                        <ChevronRight className="h-4 w-4" />
                                    </Button>
                                </Link>
                            </div>
                            
                            <div className="space-y-3">
                                {data.topValueBets.length > 0 ? (
                                    data.topValueBets.map((bet) => (
                                        <ValueBetItem key={bet.id} bet={bet} />
                                    ))
                                ) : (
                                    <p className="text-sm text-muted-foreground text-center py-4">
                                        Henüz value bet bulunamadı
                                    </p>
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Quick Stats */}
                    <Card className="bg-gradient-to-br from-primary/20 to-purple-500/20 border-primary/30">
                        <CardContent className="p-4">
                            <h3 className="font-bold mb-4 flex items-center gap-2">
                                <TrendingUp className="h-4 w-4" />
                                Sistem Durumu
                            </h3>
                            
                            <div className="space-y-3">
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-muted-foreground">Supabase</span>
                                    <span className="text-xs px-2 py-1 rounded bg-green-500/20 text-green-400">Bağlı</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-muted-foreground">Football-Data API</span>
                                    <span className="text-xs px-2 py-1 rounded bg-green-500/20 text-green-400">Aktif</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-muted-foreground">Odds Sync</span>
                                    <span className="text-xs px-2 py-1 rounded bg-green-500/20 text-green-400">Çalışıyor</span>
                                </div>
                            </div>
                            
                            <div className="mt-4 pt-4 border-t border-border/50">
                                <p className="text-xs text-muted-foreground">
                                    Son güncelleme: {new Date(data.lastUpdated).toLocaleString('tr-TR')}
                                </p>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    )
}
