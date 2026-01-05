'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface NewsItem {
    id: string
    title: string
    summary: string
    source: string
    date: string
    category: 'transfer' | 'injury' | 'match' | 'general'
    imageUrl?: string
}

const mockNews: NewsItem[] = [
    {
        id: '1',
        title: 'Liverpool confirms new signing ahead of January window',
        summary: 'The Reds are set to strengthen their squad with a key midfield addition as the January transfer window approaches.',
        source: 'Sky Sports',
        date: '2026-01-04',
        category: 'transfer'
    },
    {
        id: '2',
        title: 'Arsenal striker ruled out for 3 weeks',
        summary: 'Key forward sustains hamstring injury during training, will miss crucial Premier League fixtures.',
        source: 'BBC Sport',
        date: '2026-01-04',
        category: 'injury'
    },
    {
        id: '3',
        title: 'Manchester City extends unbeaten run to 12 games',
        summary: 'The champions continue their dominant form with another convincing victory at the Etihad.',
        source: 'The Guardian',
        date: '2026-01-03',
        category: 'match'
    },
    {
        id: '4',
        title: 'Premier League announces fixture changes for February',
        summary: 'Several top-flight matches rescheduled due to European commitments and FA Cup ties.',
        source: 'Premier League',
        date: '2026-01-03',
        category: 'general'
    },
    {
        id: '5',
        title: 'Chelsea targeting summer rebuild with new manager',
        summary: 'Blues hierarchy outlines ambitious plans for squad overhaul and playing style changes.',
        source: 'The Athletic',
        date: '2026-01-02',
        category: 'transfer'
    }
]

function NewsCard({ news }: { news: NewsItem }) {
    const categoryColors = {
        transfer: 'bg-blue-500/20 text-blue-400',
        injury: 'bg-red-500/20 text-red-400',
        match: 'bg-green-500/20 text-green-400',
        general: 'bg-gray-500/20 text-gray-400'
    }

    return (
        <Card className="bg-card/50 border-border/50 hover:border-primary/50 transition-all">
            <CardContent className="p-4">
                <div className="flex justify-between items-start mb-2">
                    <span className={`text-xs px-2 py-1 rounded-full ${categoryColors[news.category]}`}>
                        {news.category.charAt(0).toUpperCase() + news.category.slice(1)}
                    </span>
                    <span className="text-xs text-muted-foreground">{news.date}</span>
                </div>
                <h3 className="font-semibold mb-2">{news.title}</h3>
                <p className="text-sm text-muted-foreground mb-3">{news.summary}</p>
                <div className="text-xs text-primary">{news.source}</div>
            </CardContent>
        </Card>
    )
}

export default function NewsPage() {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold">News</h1>
                <p className="text-muted-foreground">Latest football news affecting predictions</p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold">{mockNews.length}</div>
                        <div className="text-sm text-muted-foreground">Total Articles</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-blue-400">
                            {mockNews.filter(n => n.category === 'transfer').length}
                        </div>
                        <div className="text-sm text-muted-foreground">Transfers</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-red-400">
                            {mockNews.filter(n => n.category === 'injury').length}
                        </div>
                        <div className="text-sm text-muted-foreground">Injuries</div>
                    </CardContent>
                </Card>
                <Card className="bg-card/50">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-green-400">
                            {mockNews.filter(n => n.category === 'match').length}
                        </div>
                        <div className="text-sm text-muted-foreground">Match Reports</div>
                    </CardContent>
                </Card>
            </div>

            {/* News Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {mockNews.map((news) => (
                    <NewsCard key={news.id} news={news} />
                ))}
            </div>
        </div>
    )
}
