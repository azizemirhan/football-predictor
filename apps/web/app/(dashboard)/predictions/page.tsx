'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'

interface Prediction {
    id: string
    homeTeam: string
    awayTeam: string
    date: string
    models: {
        ensemble: { home: number; draw: number; away: number }
        poisson: { home: number; draw: number; away: number }
        elo: { home: number; draw: number; away: number }
        xgboost: { home: number; draw: number; away: number }
    }
    expectedScore: string
    confidence: number
    keyFactors: string[]
}

const mockPredictions: Prediction[] = [
    {
        id: '1',
        homeTeam: 'Liverpool',
        awayTeam: 'Arsenal',
        date: '2026-01-05',
        models: {
            ensemble: { home: 0.45, draw: 0.28, away: 0.27 },
            poisson: { home: 0.42, draw: 0.30, away: 0.28 },
            elo: { home: 0.48, draw: 0.25, away: 0.27 },
            xgboost: { home: 0.44, draw: 0.29, away: 0.27 }
        },
        expectedScore: '2-1',
        confidence: 0.72,
        keyFactors: ['Liverpool strong home form (W4-D1-L0)', 'Arsenal key injuries', 'H2H favors home']
    },
    {
        id: '2',
        homeTeam: 'Manchester City',
        awayTeam: 'Chelsea',
        date: '2026-01-05',
        models: {
            ensemble: { home: 0.58, draw: 0.24, away: 0.18 },
            poisson: { home: 0.55, draw: 0.26, away: 0.19 },
            elo: { home: 0.62, draw: 0.22, away: 0.16 },
            xgboost: { home: 0.57, draw: 0.25, away: 0.18 }
        },
        expectedScore: '3-1',
        confidence: 0.81,
        keyFactors: ['City dominant at Etihad', 'Chelsea poor away record', 'Haaland in form']
    },
    {
        id: '3',
        homeTeam: 'Brighton',
        awayTeam: 'Wolves',
        date: '2026-01-06',
        models: {
            ensemble: { home: 0.52, draw: 0.26, away: 0.22 },
            poisson: { home: 0.49, draw: 0.28, away: 0.23 },
            elo: { home: 0.54, draw: 0.25, away: 0.21 },
            xgboost: { home: 0.53, draw: 0.25, away: 0.22 }
        },
        expectedScore: '2-1',
        confidence: 0.65,
        keyFactors: ['Brighton xG outperformance', 'Wolves defensive issues', 'Home advantage']
    }
]

function ModelBreakdown({ models }: { models: Prediction['models'] }) {
    const modelNames = ['ensemble', 'poisson', 'elo', 'xgboost'] as const
    const modelLabels = {
        ensemble: 'Ensemble',
        poisson: 'Poisson',
        elo: 'Elo Rating',
        xgboost: 'XGBoost'
    }

    return (
        <div className="space-y-3">
            {modelNames.map((name) => {
                const m = models[name]
                const winner = m.home > m.draw && m.home > m.away ? 'H' :
                    m.away > m.draw && m.away > m.home ? 'A' : 'D'
                return (
                    <div key={name} className="space-y-1">
                        <div className="flex justify-between text-xs">
                            <span className="text-muted-foreground">{modelLabels[name]}</span>
                            <span className={`font-medium ${winner === 'H' ? 'text-green-400' :
                                    winner === 'A' ? 'text-red-400' : 'text-yellow-400'
                                }`}>
                                {winner === 'H' ? 'Home' : winner === 'A' ? 'Away' : 'Draw'} ({(Math.max(m.home, m.draw, m.away) * 100).toFixed(0)}%)
                            </span>
                        </div>
                        <div className="flex h-1.5 rounded-full overflow-hidden bg-muted">
                            <div className="bg-green-500" style={{ width: `${m.home * 100}%` }} />
                            <div className="bg-yellow-500" style={{ width: `${m.draw * 100}%` }} />
                            <div className="bg-red-500" style={{ width: `${m.away * 100}%` }} />
                        </div>
                    </div>
                )
            })}
        </div>
    )
}

function PredictionCard({ prediction }: { prediction: Prediction }) {
    const [showDetails, setShowDetails] = useState(false)
    const ensemble = prediction.models.ensemble
    const predictedOutcome = ensemble.home > ensemble.draw && ensemble.home > ensemble.away ? 'Home Win' :
        ensemble.away > ensemble.draw && ensemble.away > ensemble.home ? 'Away Win' : 'Draw'

    return (
        <Card className="bg-card/50 border-border/50">
            <CardContent className="p-5">
                {/* Match Header */}
                <div className="flex justify-between items-start mb-4">
                    <div>
                        <div className="font-bold text-lg">{prediction.homeTeam} vs {prediction.awayTeam}</div>
                        <div className="text-sm text-muted-foreground">📅 {prediction.date}</div>
                    </div>
                    <div className="text-right">
                        <div className="text-xs text-muted-foreground">Confidence</div>
                        <div className="text-xl font-bold text-primary">{(prediction.confidence * 100).toFixed(0)}%</div>
                    </div>
                </div>

                {/* Main Prediction */}
                <div className="bg-primary/10 rounded-lg p-4 mb-4">
                    <div className="flex justify-between items-center">
                        <div>
                            <div className="text-sm text-muted-foreground">Predicted Outcome</div>
                            <div className="text-2xl font-bold">{predictedOutcome}</div>
                        </div>
                        <div className="text-right">
                            <div className="text-sm text-muted-foreground">Expected Score</div>
                            <div className="text-2xl font-bold">{prediction.expectedScore}</div>
                        </div>
                    </div>
                </div>

                {/* Probabilities */}
                <div className="grid grid-cols-3 gap-2 mb-4">
                    <div className="bg-green-500/10 rounded-lg p-3 text-center">
                        <div className="text-2xl font-bold text-green-400">{(ensemble.home * 100).toFixed(0)}%</div>
                        <div className="text-xs text-muted-foreground">Home</div>
                    </div>
                    <div className="bg-yellow-500/10 rounded-lg p-3 text-center">
                        <div className="text-2xl font-bold text-yellow-400">{(ensemble.draw * 100).toFixed(0)}%</div>
                        <div className="text-xs text-muted-foreground">Draw</div>
                    </div>
                    <div className="bg-red-500/10 rounded-lg p-3 text-center">
                        <div className="text-2xl font-bold text-red-400">{(ensemble.away * 100).toFixed(0)}%</div>
                        <div className="text-xs text-muted-foreground">Away</div>
                    </div>
                </div>

                {/* Key Factors */}
                <div className="mb-4">
                    <div className="text-sm font-medium mb-2">Key Factors</div>
                    <ul className="space-y-1">
                        {prediction.keyFactors.map((factor, i) => (
                            <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                                <span className="text-primary">•</span>
                                {factor}
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Model Breakdown Toggle */}
                <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={() => setShowDetails(!showDetails)}
                >
                    {showDetails ? 'Hide' : 'Show'} Model Breakdown
                </Button>

                {showDetails && (
                    <div className="mt-4 pt-4 border-t border-border/50">
                        <ModelBreakdown models={prediction.models} />
                    </div>
                )}
            </CardContent>
        </Card>
    )
}

export default function PredictionsPage() {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Predictions</h1>
                    <p className="text-muted-foreground">AI-powered match predictions with model breakdown</p>
                </div>
                <Button className="bg-primary">
                    Generate All
                </Button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold">{mockPredictions.length}</div>
                        <div className="text-sm text-muted-foreground">Active Predictions</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-green-400">58.4%</div>
                        <div className="text-sm text-muted-foreground">Accuracy (30d)</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-primary">4</div>
                        <div className="text-sm text-muted-foreground">Models Active</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold">73%</div>
                        <div className="text-sm text-muted-foreground">Avg Confidence</div>
                    </CardContent>
                </Card>
            </div>

            {/* Model Performance */}
            <Card className="bg-card/50">
                <CardHeader>
                    <CardTitle>Model Performance (Last 30 Days)</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {[
                            { name: 'Ensemble', accuracy: 58.4, color: 'bg-primary' },
                            { name: 'XGBoost', accuracy: 56.2, color: 'bg-blue-500' },
                            { name: 'Poisson', accuracy: 54.8, color: 'bg-purple-500' },
                            { name: 'Elo', accuracy: 52.1, color: 'bg-orange-500' }
                        ].map((model) => (
                            <div key={model.name} className="space-y-2">
                                <div className="flex justify-between text-sm">
                                    <span>{model.name}</span>
                                    <span className="font-medium">{model.accuracy}%</span>
                                </div>
                                <Progress value={model.accuracy} className="h-2" />
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Predictions Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {mockPredictions.map((prediction) => (
                    <PredictionCard key={prediction.id} prediction={prediction} />
                ))}
            </div>
        </div>
    )
}
