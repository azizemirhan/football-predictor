'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Input } from '@/components/ui/input'

interface Team {
    id: string
    name: string
    shortName: string
    position: number
    played: number
    won: number
    drawn: number
    lost: number
    goalsFor: number
    goalsAgainst: number
    points: number
    form: string
    elo: number
    attackStrength: number
    defenseStrength: number
}

const mockTeams: Team[] = [
    { id: '1', name: 'Liverpool', shortName: 'LIV', position: 1, played: 20, won: 15, drawn: 3, lost: 2, goalsFor: 48, goalsAgainst: 18, points: 48, form: 'WWDWW', elo: 1892, attackStrength: 1.45, defenseStrength: 0.72 },
    { id: '2', name: 'Arsenal', shortName: 'ARS', position: 2, played: 20, won: 13, drawn: 5, lost: 2, goalsFor: 42, goalsAgainst: 20, points: 44, form: 'WDWWW', elo: 1865, attackStrength: 1.38, defenseStrength: 0.78 },
    { id: '3', name: 'Manchester City', shortName: 'MCI', position: 3, played: 20, won: 13, drawn: 4, lost: 3, goalsFor: 45, goalsAgainst: 22, points: 43, form: 'DWWLW', elo: 1878, attackStrength: 1.42, defenseStrength: 0.82 },
    { id: '4', name: 'Chelsea', shortName: 'CHE', position: 4, played: 20, won: 11, drawn: 5, lost: 4, goalsFor: 38, goalsAgainst: 24, points: 38, form: 'WDWLD', elo: 1742, attackStrength: 1.18, defenseStrength: 0.88 },
    { id: '5', name: 'Newcastle', shortName: 'NEW', position: 5, played: 20, won: 10, drawn: 6, lost: 4, goalsFor: 35, goalsAgainst: 22, points: 36, form: 'DDWWL', elo: 1728, attackStrength: 1.12, defenseStrength: 0.85 },
    { id: '6', name: 'Aston Villa', shortName: 'AVL', position: 6, played: 20, won: 10, drawn: 5, lost: 5, goalsFor: 34, goalsAgainst: 26, points: 35, form: 'WLWDW', elo: 1695, attackStrength: 1.08, defenseStrength: 0.92 },
    { id: '7', name: 'Tottenham', shortName: 'TOT', position: 7, played: 20, won: 9, drawn: 5, lost: 6, goalsFor: 38, goalsAgainst: 28, points: 32, form: 'LDWWD', elo: 1682, attackStrength: 1.15, defenseStrength: 0.98 },
    { id: '8', name: 'Brighton', shortName: 'BHA', position: 8, played: 20, won: 8, drawn: 7, lost: 5, goalsFor: 32, goalsAgainst: 28, points: 31, form: 'DWDWL', elo: 1658, attackStrength: 1.02, defenseStrength: 0.95 },
]

function TeamRow({ team, rank }: { team: Team; rank: number }) {
    const formColors: Record<string, string> = {
        'W': 'bg-green-500',
        'D': 'bg-yellow-500',
        'L': 'bg-red-500'
    }

    return (
        <div className="grid grid-cols-12 gap-4 items-center p-4 hover:bg-muted/30 rounded-lg transition-colors">
            {/* Position */}
            <div className="col-span-1 text-center">
                <span className={`font-bold ${rank <= 4 ? 'text-green-400' : rank >= 18 ? 'text-red-400' : ''}`}>
                    {team.position}
                </span>
            </div>

            {/* Team */}
            <div className="col-span-3">
                <div className="font-semibold">{team.name}</div>
                <div className="text-xs text-muted-foreground">Elo: {team.elo}</div>
            </div>

            {/* Stats */}
            <div className="col-span-1 text-center text-sm">{team.played}</div>
            <div className="col-span-1 text-center text-sm">{team.won}</div>
            <div className="col-span-1 text-center text-sm">{team.drawn}</div>
            <div className="col-span-1 text-center text-sm">{team.lost}</div>
            <div className="col-span-1 text-center text-sm">{team.goalsFor}-{team.goalsAgainst}</div>

            {/* Points */}
            <div className="col-span-1 text-center">
                <span className="font-bold text-primary">{team.points}</span>
            </div>

            {/* Form */}
            <div className="col-span-2 flex gap-1 justify-end">
                {team.form.split('').map((result, i) => (
                    <span
                        key={i}
                        className={`w-6 h-6 rounded flex items-center justify-center text-xs font-medium ${formColors[result]}`}
                    >
                        {result}
                    </span>
                ))}
            </div>
        </div>
    )
}

function TeamCard({ team }: { team: Team }) {
    const gd = team.goalsFor - team.goalsAgainst

    return (
        <Card className="bg-card/50 border-border/50 hover:border-primary/50 transition-all">
            <CardContent className="p-4">
                <div className="flex justify-between items-start mb-4">
                    <div>
                        <div className="text-lg font-bold">{team.name}</div>
                        <div className="text-sm text-muted-foreground">Position: #{team.position}</div>
                    </div>
                    <div className="text-right">
                        <div className="text-2xl font-bold text-primary">{team.points}</div>
                        <div className="text-xs text-muted-foreground">points</div>
                    </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-4 gap-2 mb-4 text-center">
                    <div className="bg-muted/30 p-2 rounded">
                        <div className="text-lg font-bold">{team.won}</div>
                        <div className="text-xs text-muted-foreground">W</div>
                    </div>
                    <div className="bg-muted/30 p-2 rounded">
                        <div className="text-lg font-bold">{team.drawn}</div>
                        <div className="text-xs text-muted-foreground">D</div>
                    </div>
                    <div className="bg-muted/30 p-2 rounded">
                        <div className="text-lg font-bold">{team.lost}</div>
                        <div className="text-xs text-muted-foreground">L</div>
                    </div>
                    <div className="bg-muted/30 p-2 rounded">
                        <div className={`text-lg font-bold ${gd > 0 ? 'text-green-400' : gd < 0 ? 'text-red-400' : ''}`}>
                            {gd > 0 ? '+' : ''}{gd}
                        </div>
                        <div className="text-xs text-muted-foreground">GD</div>
                    </div>
                </div>

                {/* Ratings */}
                <div className="space-y-2">
                    <div>
                        <div className="flex justify-between text-xs mb-1">
                            <span>Attack</span>
                            <span className="text-green-400">{team.attackStrength.toFixed(2)}</span>
                        </div>
                        <Progress value={team.attackStrength * 50} className="h-2" />
                    </div>
                    <div>
                        <div className="flex justify-between text-xs mb-1">
                            <span>Defense</span>
                            <span className="text-blue-400">{team.defenseStrength.toFixed(2)}</span>
                        </div>
                        <Progress value={(2 - team.defenseStrength) * 50} className="h-2" />
                    </div>
                </div>

                {/* Elo */}
                <div className="mt-4 pt-4 border-t border-border/50 flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Elo Rating</span>
                    <span className="text-xl font-bold">{team.elo}</span>
                </div>
            </CardContent>
        </Card>
    )
}

export default function TeamsPage() {
    const [view, setView] = useState<'table' | 'cards'>('table')
    const [search, setSearch] = useState('')

    const filteredTeams = mockTeams.filter(team =>
        team.name.toLowerCase().includes(search.toLowerCase())
    )

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Teams</h1>
                    <p className="text-muted-foreground">Premier League standings and team ratings</p>
                </div>
                <div className="flex gap-2">
                    <Button
                        variant={view === 'table' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setView('table')}
                    >
                        Table
                    </Button>
                    <Button
                        variant={view === 'cards' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setView('cards')}
                    >
                        Cards
                    </Button>
                </div>
            </div>

            {/* Search */}
            <Input
                placeholder="Search teams..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="max-w-md"
            />

            {view === 'table' ? (
                <Card className="bg-card/50">
                    <CardContent className="p-0">
                        {/* Header */}
                        <div className="grid grid-cols-12 gap-4 p-4 border-b border-border/50 text-sm text-muted-foreground">
                            <div className="col-span-1 text-center">#</div>
                            <div className="col-span-3">Team</div>
                            <div className="col-span-1 text-center">P</div>
                            <div className="col-span-1 text-center">W</div>
                            <div className="col-span-1 text-center">D</div>
                            <div className="col-span-1 text-center">L</div>
                            <div className="col-span-1 text-center">G</div>
                            <div className="col-span-1 text-center">Pts</div>
                            <div className="col-span-2 text-right">Form</div>
                        </div>

                        {/* Rows */}
                        <div className="divide-y divide-border/30">
                            {filteredTeams.map((team, i) => (
                                <TeamRow key={team.id} team={team} rank={i + 1} />
                            ))}
                        </div>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {filteredTeams.map((team) => (
                        <TeamCard key={team.id} team={team} />
                    ))}
                </div>
            )}
        </div>
    )
}
