'use client'

import { useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'

interface Player {
    id: string
    name: string
    team: string
    position: string
    goals: number
    assists: number
    matches: number
    rating: number
    form: number
    injuryStatus: 'fit' | 'doubtful' | 'injured'
}

const mockPlayers: Player[] = [
    { id: '1', name: 'Erling Haaland', team: 'Manchester City', position: 'ST', goals: 18, assists: 5, matches: 20, rating: 8.2, form: 92, injuryStatus: 'fit' },
    { id: '2', name: 'Mohamed Salah', team: 'Liverpool', position: 'RW', goals: 15, assists: 10, matches: 20, rating: 8.0, form: 88, injuryStatus: 'fit' },
    { id: '3', name: 'Bukayo Saka', team: 'Arsenal', position: 'RW', goals: 10, assists: 8, matches: 19, rating: 7.8, form: 85, injuryStatus: 'fit' },
    { id: '4', name: 'Cole Palmer', team: 'Chelsea', position: 'AM', goals: 12, assists: 6, matches: 20, rating: 7.7, form: 82, injuryStatus: 'fit' },
    { id: '5', name: 'Alexander Isak', team: 'Newcastle', position: 'ST', goals: 11, assists: 3, matches: 18, rating: 7.5, form: 78, injuryStatus: 'doubtful' },
    { id: '6', name: 'Ollie Watkins', team: 'Aston Villa', position: 'ST', goals: 9, assists: 7, matches: 20, rating: 7.4, form: 75, injuryStatus: 'fit' },
    { id: '7', name: 'Son Heung-min', team: 'Tottenham', position: 'LW', goals: 8, assists: 5, matches: 17, rating: 7.3, form: 70, injuryStatus: 'injured' },
    { id: '8', name: 'Bruno Fernandes', team: 'Manchester United', position: 'AM', goals: 6, assists: 8, matches: 20, rating: 7.2, form: 68, injuryStatus: 'fit' },
]

function PlayerCard({ player }: { player: Player }) {
    const injuryColors = {
        fit: 'bg-green-500/20 text-green-400',
        doubtful: 'bg-yellow-500/20 text-yellow-400',
        injured: 'bg-red-500/20 text-red-400'
    }

    return (
        <Card className="bg-card/50 border-border/50 hover:border-primary/50 transition-all">
            <CardContent className="p-4">
                <div className="flex justify-between items-start mb-3">
                    <div>
                        <div className="font-semibold">{player.name}</div>
                        <div className="text-sm text-muted-foreground">{player.team} • {player.position}</div>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${injuryColors[player.injuryStatus]}`}>
                        {player.injuryStatus.charAt(0).toUpperCase() + player.injuryStatus.slice(1)}
                    </span>
                </div>

                <div className="grid grid-cols-4 gap-2 mb-3 text-center">
                    <div className="bg-muted/30 p-2 rounded">
                        <div className="text-lg font-bold">{player.goals}</div>
                        <div className="text-xs text-muted-foreground">Goals</div>
                    </div>
                    <div className="bg-muted/30 p-2 rounded">
                        <div className="text-lg font-bold">{player.assists}</div>
                        <div className="text-xs text-muted-foreground">Assists</div>
                    </div>
                    <div className="bg-muted/30 p-2 rounded">
                        <div className="text-lg font-bold">{player.matches}</div>
                        <div className="text-xs text-muted-foreground">Matches</div>
                    </div>
                    <div className="bg-muted/30 p-2 rounded">
                        <div className="text-lg font-bold text-primary">{player.rating}</div>
                        <div className="text-xs text-muted-foreground">Rating</div>
                    </div>
                </div>

                <div>
                    <div className="flex justify-between text-xs mb-1">
                        <span className="text-muted-foreground">Form</span>
                        <span>{player.form}%</span>
                    </div>
                    <Progress value={player.form} className="h-2" />
                </div>
            </CardContent>
        </Card>
    )
}

export default function PlayersPage() {
    const [search, setSearch] = useState('')

    const filteredPlayers = mockPlayers.filter(player =>
        player.name.toLowerCase().includes(search.toLowerCase()) ||
        player.team.toLowerCase().includes(search.toLowerCase())
    )

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold">Players</h1>
                <p className="text-muted-foreground">Player statistics and form tracking</p>
            </div>

            {/* Search */}
            <Input
                placeholder="Search players or teams..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="max-w-md"
            />

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold">{mockPlayers.length}</div>
                        <div className="text-sm text-muted-foreground">Total Players</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-green-400">
                            {mockPlayers.filter(p => p.injuryStatus === 'fit').length}
                        </div>
                        <div className="text-sm text-muted-foreground">Fit</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-yellow-400">
                            {mockPlayers.filter(p => p.injuryStatus === 'doubtful').length}
                        </div>
                        <div className="text-sm text-muted-foreground">Doubtful</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-red-400">
                            {mockPlayers.filter(p => p.injuryStatus === 'injured').length}
                        </div>
                        <div className="text-sm text-muted-foreground">Injured</div>
                    </CardContent>
                </Card>
            </div>

            {/* Players Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {filteredPlayers.map((player) => (
                    <PlayerCard key={player.id} player={player} />
                ))}
            </div>
        </div>
    )
}
