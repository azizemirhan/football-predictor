'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'

export default function AnalyticsPage() {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold">Analytics</h1>
                <p className="text-muted-foreground">Model performance and betting statistics</p>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="bg-gradient-to-br from-green-500/20 to-green-500/5">
                    <CardContent className="p-6">
                        <div className="text-sm text-muted-foreground">Overall Accuracy</div>
                        <div className="text-4xl font-bold text-green-400">58.4%</div>
                        <div className="text-xs text-green-400 mt-1">▲ +2.1% from last month</div>
                    </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-blue-500/20 to-blue-500/5">
                    <CardContent className="p-6">
                        <div className="text-sm text-muted-foreground">Total Predictions</div>
                        <div className="text-4xl font-bold">1,247</div>
                        <div className="text-xs text-muted-foreground mt-1">Since inception</div>
                    </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-primary/20 to-primary/5">
                    <CardContent className="p-6">
                        <div className="text-sm text-muted-foreground">Betting ROI</div>
                        <div className="text-4xl font-bold text-primary">+12.5%</div>
                        <div className="text-xs text-primary mt-1">Last 30 days</div>
                    </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-purple-500/20 to-purple-500/5">
                    <CardContent className="p-6">
                        <div className="text-sm text-muted-foreground">Value Bets Hit Rate</div>
                        <div className="text-4xl font-bold text-purple-400">67%</div>
                        <div className="text-xs text-muted-foreground mt-1">Edge &gt; 5%</div>
                    </CardContent>
                </Card>
            </div>

            {/* Model Performance Comparison */}
            <Card className="bg-card/50">
                <CardHeader>
                    <CardTitle>Model Performance Comparison</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-6">
                        {[
                            { name: 'Ensemble', accuracy: 58.4, logLoss: 0.92, brier: 0.21, roi: 12.5, color: 'bg-primary' },
                            { name: 'XGBoost', accuracy: 56.2, logLoss: 0.95, brier: 0.22, roi: 8.3, color: 'bg-blue-500' },
                            { name: 'Poisson', accuracy: 54.8, logLoss: 0.98, brier: 0.23, roi: 5.1, color: 'bg-purple-500' },
                            { name: 'Elo', accuracy: 52.1, logLoss: 1.02, brier: 0.24, roi: 2.8, color: 'bg-orange-500' }
                        ].map((model) => (
                            <div key={model.name} className="grid grid-cols-5 gap-4 items-center">
                                <div className="font-medium">{model.name}</div>
                                <div>
                                    <div className="flex justify-between text-xs mb-1">
                                        <span className="text-muted-foreground">Accuracy</span>
                                        <span>{model.accuracy}%</span>
                                    </div>
                                    <Progress value={model.accuracy} className="h-2" />
                                </div>
                                <div>
                                    <div className="flex justify-between text-xs mb-1">
                                        <span className="text-muted-foreground">Log Loss</span>
                                        <span>{model.logLoss}</span>
                                    </div>
                                    <Progress value={(1 - model.logLoss) * 100} className="h-2" />
                                </div>
                                <div>
                                    <div className="flex justify-between text-xs mb-1">
                                        <span className="text-muted-foreground">Brier Score</span>
                                        <span>{model.brier}</span>
                                    </div>
                                    <Progress value={(1 - model.brier) * 100} className="h-2" />
                                </div>
                                <div className={`text-right font-bold ${model.roi > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                    {model.roi > 0 ? '+' : ''}{model.roi}% ROI
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Accuracy Trend */}
                <Card className="bg-card/50">
                    <CardHeader>
                        <CardTitle>Accuracy Trend (Last 12 Weeks)</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="h-64 flex items-end justify-between gap-2">
                            {[52, 54, 51, 56, 58, 55, 57, 59, 56, 58, 60, 58].map((value, i) => (
                                <div key={i} className="flex-1 flex flex-col items-center gap-2">
                                    <div
                                        className="w-full bg-primary/80 rounded-t hover:bg-primary transition-colors"
                                        style={{ height: `${value * 3}px` }}
                                    />
                                    <span className="text-xs text-muted-foreground">W{i + 1}</span>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* Profit/Loss */}
                <Card className="bg-card/50">
                    <CardHeader>
                        <CardTitle>Cumulative P/L (Units)</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="h-64 flex items-end justify-between gap-2">
                            {[2, 5, 3, 8, 12, 10, 15, 18, 16, 20, 25, 28].map((value, i) => (
                                <div key={i} className="flex-1 flex flex-col items-center gap-2">
                                    <div
                                        className="w-full bg-green-500/80 rounded-t hover:bg-green-500 transition-colors"
                                        style={{ height: `${value * 7}px` }}
                                    />
                                    <span className="text-xs text-muted-foreground">W{i + 1}</span>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Breakdown Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* By Outcome */}
                <Card className="bg-card/50">
                    <CardHeader>
                        <CardTitle>Accuracy by Outcome</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span>Home Wins</span>
                                <span className="font-medium text-green-400">62%</span>
                            </div>
                            <Progress value={62} className="h-2" />
                        </div>
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span>Draws</span>
                                <span className="font-medium text-yellow-400">38%</span>
                            </div>
                            <Progress value={38} className="h-2" />
                        </div>
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span>Away Wins</span>
                                <span className="font-medium text-blue-400">55%</span>
                            </div>
                            <Progress value={55} className="h-2" />
                        </div>
                    </CardContent>
                </Card>

                {/* By Confidence */}
                <Card className="bg-card/50">
                    <CardHeader>
                        <CardTitle>Accuracy by Confidence</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span>High (&gt;70%)</span>
                                <span className="font-medium text-green-400">71%</span>
                            </div>
                            <Progress value={71} className="h-2" />
                        </div>
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span>Medium (50-70%)</span>
                                <span className="font-medium text-yellow-400">56%</span>
                            </div>
                            <Progress value={56} className="h-2" />
                        </div>
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span>Low (&lt;50%)</span>
                                <span className="font-medium text-red-400">42%</span>
                            </div>
                            <Progress value={42} className="h-2" />
                        </div>
                    </CardContent>
                </Card>

                {/* By Edge */}
                <Card className="bg-card/50">
                    <CardHeader>
                        <CardTitle>Value Bet Performance</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span>Edge &gt;10%</span>
                                <span className="font-medium text-green-400">72%</span>
                            </div>
                            <Progress value={72} className="h-2" />
                        </div>
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span>Edge 5-10%</span>
                                <span className="font-medium text-yellow-400">61%</span>
                            </div>
                            <Progress value={61} className="h-2" />
                        </div>
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span>Edge 3-5%</span>
                                <span className="font-medium text-orange-400">54%</span>
                            </div>
                            <Progress value={54} className="h-2" />
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Recent Predictions */}
            <Card className="bg-card/50">
                <CardHeader>
                    <CardTitle>Recent Prediction Results</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-3">
                        {[
                            { match: 'Liverpool 2-1 Arsenal', prediction: 'Home Win', confidence: 72, result: 'Correct' },
                            { match: 'Man City 3-0 Chelsea', prediction: 'Home Win', confidence: 81, result: 'Correct' },
                            { match: 'Tottenham 1-1 Newcastle', prediction: 'Home Win', confidence: 58, result: 'Wrong' },
                            { match: 'Brighton 2-1 Wolves', prediction: 'Home Win', confidence: 65, result: 'Correct' },
                            { match: 'Everton 0-0 West Ham', prediction: 'Draw', confidence: 52, result: 'Correct' }
                        ].map((pred, i) => (
                            <div key={i} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                                <div>
                                    <div className="font-medium">{pred.match}</div>
                                    <div className="text-sm text-muted-foreground">
                                        Predicted: {pred.prediction} ({pred.confidence}% confidence)
                                    </div>
                                </div>
                                <span className={`px-3 py-1 rounded-full text-sm ${pred.result === 'Correct'
                                        ? 'bg-green-500/20 text-green-400'
                                        : 'bg-red-500/20 text-red-400'
                                    }`}>
                                    {pred.result}
                                </span>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
