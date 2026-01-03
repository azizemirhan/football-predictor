import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
    TrendingUp,
    TrendingDown,
    Target,
    Zap,
    Calendar,
    ChevronRight,
    Trophy
} from "lucide-react"

// Stat Card Component
function StatCard({
    title,
    value,
    change,
    changeType,
    icon: Icon
}: {
    title: string
    value: string
    change: string
    changeType: "up" | "down"
    icon: React.ElementType
}) {
    return (
        <Card>
            <CardContent className="p-6">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm text-muted-foreground">{title}</p>
                        <p className="text-2xl font-bold mt-1">{value}</p>
                        <div className="flex items-center gap-1 mt-2">
                            {changeType === "up" ? (
                                <TrendingUp className="h-4 w-4 text-green-500" />
                            ) : (
                                <TrendingDown className="h-4 w-4 text-red-500" />
                            )}
                            <span className={changeType === "up" ? "text-green-500 text-sm" : "text-red-500 text-sm"}>
                                {change}
                            </span>
                        </div>
                    </div>
                    <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                        <Icon className="h-6 w-6 text-primary" />
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}

// Upcoming Match Component
function UpcomingMatch({
    homeTeam,
    awayTeam,
    time,
    prediction
}: {
    homeTeam: string
    awayTeam: string
    time: string
    prediction: { home: number; draw: number; away: number }
}) {
    return (
        <div className="match-card">
            <div className="flex items-center justify-between mb-4">
                <span className="text-xs text-muted-foreground">{time}</span>
                <span className="prediction-badge prediction-badge-high">High Confidence</span>
            </div>

            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center">
                        <Trophy className="h-5 w-5" />
                    </div>
                    <span className="font-medium">{homeTeam}</span>
                </div>
                <span className="text-muted-foreground">vs</span>
                <div className="flex items-center gap-3">
                    <span className="font-medium">{awayTeam}</span>
                    <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center">
                        <Trophy className="h-5 w-5" />
                    </div>
                </div>
            </div>

            <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                    <span>Home Win</span>
                    <span className="font-medium">{prediction.home}%</span>
                </div>
                <Progress value={prediction.home} className="h-2" />

                <div className="flex items-center justify-between text-sm">
                    <span>Draw</span>
                    <span className="font-medium">{prediction.draw}%</span>
                </div>
                <Progress value={prediction.draw} className="h-2" />

                <div className="flex items-center justify-between text-sm">
                    <span>Away Win</span>
                    <span className="font-medium">{prediction.away}%</span>
                </div>
                <Progress value={prediction.away} className="h-2" />
            </div>
        </div>
    )
}

// Value Bet Component
function ValueBetCard({
    match,
    selection,
    odds,
    edge,
    confidence
}: {
    match: string
    selection: string
    odds: number
    edge: number
    confidence: string
}) {
    return (
        <div className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors">
            <div className="flex-1">
                <p className="font-medium">{match}</p>
                <p className="text-sm text-muted-foreground">{selection}</p>
            </div>
            <div className="text-right">
                <p className="font-bold text-primary">{odds.toFixed(2)}</p>
                <p className="text-xs text-green-500">+{(edge * 100).toFixed(1)}% edge</p>
            </div>
            <ChevronRight className="h-5 w-5 text-muted-foreground ml-2" />
        </div>
    )
}

export default function DashboardPage() {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold">Dashboard</h1>
                <p className="text-muted-foreground mt-1">
                    Welcome back! Here&apos;s your prediction overview.
                </p>
            </div>

            {/* Stats Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <StatCard
                    title="Accuracy (30d)"
                    value="58.4%"
                    change="+2.3% from last month"
                    changeType="up"
                    icon={Target}
                />
                <StatCard
                    title="ROI (30d)"
                    value="+12.5%"
                    change="+4.2% from last month"
                    changeType="up"
                    icon={TrendingUp}
                />
                <StatCard
                    title="Value Bets Found"
                    value="23"
                    change="5 new today"
                    changeType="up"
                    icon={Zap}
                />
                <StatCard
                    title="Upcoming Matches"
                    value="12"
                    change="Next 48 hours"
                    changeType="up"
                    icon={Calendar}
                />
            </div>

            {/* Main Content Grid */}
            <div className="grid gap-6 lg:grid-cols-3">
                {/* Upcoming Matches */}
                <div className="lg:col-span-2 space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-semibold">Upcoming Matches</h2>
                        <Button variant="ghost" size="sm">
                            View All <ChevronRight className="h-4 w-4 ml-1" />
                        </Button>
                    </div>

                    <div className="grid gap-4 md:grid-cols-2">
                        <UpcomingMatch
                            homeTeam="Liverpool"
                            awayTeam="Arsenal"
                            time="Tomorrow, 15:00"
                            prediction={{ home: 45, draw: 28, away: 27 }}
                        />
                        <UpcomingMatch
                            homeTeam="Man City"
                            awayTeam="Chelsea"
                            time="Sunday, 17:30"
                            prediction={{ home: 62, draw: 22, away: 16 }}
                        />
                    </div>
                </div>

                {/* Value Bets */}
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-semibold">Top Value Bets</h2>
                        <Button variant="ghost" size="sm">
                            View All <ChevronRight className="h-4 w-4 ml-1" />
                        </Button>
                    </div>

                    <Card>
                        <CardContent className="p-4 space-y-3">
                            <ValueBetCard
                                match="Liverpool vs Arsenal"
                                selection="Home Win"
                                odds={2.15}
                                edge={0.072}
                                confidence="high"
                            />
                            <ValueBetCard
                                match="Brighton vs Newcastle"
                                selection="Over 2.5"
                                odds={1.85}
                                edge={0.054}
                                confidence="medium"
                            />
                            <ValueBetCard
                                match="Aston Villa vs Wolves"
                                selection="BTTS Yes"
                                odds={1.72}
                                edge={0.048}
                                confidence="medium"
                            />
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* Model Performance */}
            <Card>
                <CardHeader>
                    <CardTitle>Model Performance (Last 30 Days)</CardTitle>
                    <CardDescription>
                        Breakdown by prediction model
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid gap-4 md:grid-cols-4">
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <span className="text-sm">Ensemble</span>
                                <span className="text-sm font-medium">58.4%</span>
                            </div>
                            <Progress value={58.4} className="h-2" />
                        </div>
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <span className="text-sm">XGBoost</span>
                                <span className="text-sm font-medium">55.2%</span>
                            </div>
                            <Progress value={55.2} className="h-2" />
                        </div>
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <span className="text-sm">Poisson</span>
                                <span className="text-sm font-medium">52.8%</span>
                            </div>
                            <Progress value={52.8} className="h-2" />
                        </div>
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <span className="text-sm">Elo Rating</span>
                                <span className="text-sm font-medium">51.6%</span>
                            </div>
                            <Progress value={51.6} className="h-2" />
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
