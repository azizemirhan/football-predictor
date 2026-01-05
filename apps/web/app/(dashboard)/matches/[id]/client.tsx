'use client'

import { useState, useEffect } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { AlertCircle, UserX, Activity, Shirt, TrendingUp } from 'lucide-react'

// Market name translations (English to Turkish + mtid fallback)
const MARKET_NAMES_TR: Record<string, string> = {
  // English market types from existing data
  'MATCH_RESULT': 'Maç Sonucu',
  'BTTS': 'Karşılıklı Gol',
  'DOUBLE_CHANCE': 'Çifte Şans',
  'FIRST_HALF_RESULT': 'İlk Yarı Sonucu',
  'FIRST_HALF_1X2': 'İlk Yarı 1X2',
  'HANDICAP': 'Handikap',
  'ODD_EVEN': 'Tek/Çift',
  'OVER_UNDER_0_5': 'Alt/Üst 0.5',
  'OVER_UNDER_1_5': 'Alt/Üst 1.5',
  'OVER_UNDER_2_5': 'Alt/Üst 2.5',
  'OVER_UNDER_3_5': 'Alt/Üst 3.5',
  'BOTH_HALVES_GOAL': 'Her İki Yarıda Gol',
  'HOME_GOALS_1_5': 'Ev Sahibi Alt/Üst 1.5',
  'HOME_GOALS_HALF': 'Ev Sahibi İlk Yarı Alt/Üst',
  'AWAY_GOALS_0_5': 'Deplasman Alt/Üst 0.5',
  'AWAY_GOALS_HALF': 'Deplasman İlk Yarı Alt/Üst',
  'CORRECT_SCORE': 'Doğru Skor',
  'FIRST_HALF_OVER_UNDER': 'İlk Yarı Alt/Üst',
  'RESULT_OVER_UNDER': 'Sonuç & Alt/Üst',
  'HT_FT': 'İlk Yarı / Maç Sonucu',
  'TEAM_GOALS': 'Takım Golleri',
  // MTID-based unknowns (Iddaa st codes)
  'UNKNOWN_4': 'Toplam Gol Aralığı',
  'UNKNOWN_6': 'İlk Gol',
  'UNKNOWN_7': 'Maç Sonucu & Alt/Üst',
  'UNKNOWN_48': 'Ev Sahibi Alt/Üst',
  'UNKNOWN_49': 'Deplasman Alt/Üst',
  'UNKNOWN_69': 'Penaltı Var/Yok',
  'UNKNOWN_72': 'Kırmızı Kart Var/Yok',
  'UNKNOWN_90': 'İlk Yarı / Maç Sonucu',
  'UNKNOWN_698': 'Maç Sonucu & Karşılıklı Gol',
  'UNKNOWN_699': 'İlk Yarı & Karşılıklı Gol',
  'UNKNOWN_700': 'Alt/Üst & Karşılıklı Gol',
}

function translateMarketName(name: string): string {
  // Check direct translation
  if (MARKET_NAMES_TR[name]) return MARKET_NAMES_TR[name]
  // Check with underscores replaced
  const normalized = name.replace(/_/g, ' ')
  // If already Turkish or unknown, return as-is but clean underscores
  return normalized
}

interface MatchDetailsClientProps {
  fixture: any
  injuries: any[]
  stats: any[]
  lineups: any[]
  predictions: any[]
  fixtureId: string  // External fixture ID for fetching markets
}

export function MatchDetailsClient({ fixture, injuries, stats, lineups, predictions, fixtureId }: MatchDetailsClientProps) {
  const [markets, setMarkets] = useState<Record<string, any[]>>({})
  const [marketsLoading, setMarketsLoading] = useState(false)
  const [activeBookmaker, setActiveBookmaker] = useState<string>('Nesine')

  // Fetch markets when switching to Oranlar tab
  const fetchMarkets = async () => {
    if (Object.keys(markets).length > 0) return // Already loaded
    setMarketsLoading(true)
    try {
      const res = await fetch(`/api/match-markets/${fixtureId}`)
      const data = await res.json()
      setMarkets(data.markets || {})
      if (Object.keys(data.markets || {}).length > 0) {
        setActiveBookmaker(Object.keys(data.markets)[0])
      }
    } catch (e) {
      console.error('Failed to load markets:', e)
    } finally {
      setMarketsLoading(false)
    }
  }

  return (
    <Tabs defaultValue="overview" className="w-full">
      <TabsList className="grid w-full grid-cols-6">
        <TabsTrigger value="overview">Genel Bakış</TabsTrigger>
        <TabsTrigger value="oranlar" onClick={fetchMarkets}>Oranlar</TabsTrigger>
        <TabsTrigger value="lineups">Kadrolar</TabsTrigger>
        <TabsTrigger value="stats">İstatistikler</TabsTrigger>
        <TabsTrigger value="injuries">Sakatlıklar</TabsTrigger>
        <TabsTrigger value="predictions">Tahminler</TabsTrigger>
      </TabsList>

      <TabsContent value="overview" className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Maç Özeti</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center p-8 text-muted-foreground">
              Maç özeti yakında...
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      {/* Oranlar Tab */}
      <TabsContent value="oranlar" className="space-y-4">
        {marketsLoading ? (
          <div className="flex items-center justify-center p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary"></div>
          </div>
        ) : Object.keys(markets).length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center text-muted-foreground">
              Bu maç için oran bilgisi bulunamadı.
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {/* Bookmaker Tabs */}
            <div className="flex gap-2 mb-4">
              {Object.keys(markets).map((bm) => (
                <button
                  key={bm}
                  onClick={() => setActiveBookmaker(bm)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    activeBookmaker === bm
                      ? 'bg-emerald-500 text-white'
                      : 'bg-card border hover:bg-emerald-500/10'
                  }`}
                >
                  {bm}
                </button>
              ))}
            </div>

            {/* Market Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {(markets[activeBookmaker] || []).map((market: any) => (
                <Card key={market.mtid} className="overflow-hidden">
                  <CardHeader className="py-3 bg-gradient-to-r from-emerald-500/10 to-transparent border-b">
                    <CardTitle className="text-sm font-medium">
                      {translateMarketName(market.marketType)}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="py-3">
                    <div className="grid grid-cols-2 gap-2">
                      {market.outcomes?.slice(0, 6).map((o: any, idx: number) => (
                        <div
                          key={idx}
                          className="flex justify-between items-center p-2 bg-background/50 rounded border hover:border-emerald-500/50 transition-colors cursor-pointer"
                        >
                          <span className="text-xs text-muted-foreground truncate mr-2">{o.name}</span>
                          <span className="font-bold text-sm">{o.odds?.toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                    {market.outcomes?.length > 6 && (
                      <div className="text-center text-xs text-muted-foreground mt-2">
                        +{market.outcomes.length - 6} daha fazla
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
      </TabsContent>

      <TabsContent value="lineups" className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {lineups?.map((teamLineup: any) => (
            <Card key={teamLineup.team.id}>
              <CardHeader className="flex flex-row items-center space-x-4 pb-2">
                <img src={teamLineup.team.logo} className="w-8 h-8" alt={teamLineup.team.name} />
                <CardTitle className="text-base">{teamLineup.team.name}</CardTitle>
                <span className="text-xs text-muted-foreground ml-auto">{teamLineup.formation}</span>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div>
                    <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                      <Shirt className="w-4 h-4" /> İlk 11
                    </h4>
                    <div className="space-y-1">
                      {teamLineup.startXI.map((player: any) => (
                        <div key={player.player.id} className="flex items-center justify-between text-sm py-1 border-b border-border/50 last:border-0">
                          <span className="w-6 text-muted-foreground text-xs">{player.player.number}</span>
                          <span className="font-medium">{player.player.name}</span>
                          <span className="text-xs text-muted-foreground">{player.player.pos}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold mb-2 text-muted-foreground">Yedekler</h4>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                      {teamLineup.substitutes.map((player: any) => (
                        <div key={player.player.id} className="text-xs text-muted-foreground truncate">
                          {player.player.number} {player.player.name}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          {(!lineups || lineups.length === 0) && (
            <Card className="col-span-2">
              <CardContent className="p-8 text-center text-muted-foreground">
                Kadro bilgisi henüz açıklanmadı.
              </CardContent>
            </Card>
          )}
        </div>
      </TabsContent>

      <TabsContent value="stats" className="space-y-4">
        <div className="grid gap-4">
           {stats?.map((teamStats: any) => (
             <Card key={teamStats.team.id}>
               <CardHeader className="flex flex-row items-center space-x-4 pb-2">
                 <img src={teamStats.team.logo} className="w-6 h-6" alt={teamStats.team.name} />
                 <CardTitle className="text-base">{teamStats.team.name}</CardTitle>
               </CardHeader>
               <CardContent className="space-y-2">
                 {teamStats.statistics.map((stat: any) => (
                   <div key={stat.type} className="flex items-center justify-between text-sm">
                     <span className="text-muted-foreground">{stat.type}</span>
                     <span className="font-bold">{stat.value ?? 0}</span>
                   </div>
                 ))}
               </CardContent>
             </Card>
           ))}
           {(!stats || stats.length === 0) && (
             <Card>
               <CardContent className="p-8 text-center text-muted-foreground">
                 İstatistik bulunamadı.
               </CardContent>
             </Card>
           )}
        </div>
      </TabsContent>

      <TabsContent value="injuries" className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-red-500" />
              Sakat & Cezalı Raporu
            </CardTitle>
          </CardHeader>
          <CardContent>
            {injuries && injuries.length > 0 ? (
              <div className="space-y-4">
                {/* Group by team */}
                {Object.values(injuries.reduce((acc: any, inj: any) => {
                  if (!acc[inj.team.id]) acc[inj.team.id] = { team: inj.team, players: [] }
                  acc[inj.team.id].players.push(inj)
                  return acc
                }, {})).map((group: any) => (
                  <div key={group.team.id} className="space-y-2">
                    <div className="flex items-center gap-2 font-semibold bg-secondary/20 p-2 rounded">
                      <img src={group.team.logo} className="w-5 h-5" alt={group.team.name} />
                      {group.team.name}
                    </div>
                    <div className="grid gap-2">
                      {group.players.map((inj: any) => (
                        <div key={inj.player.id} className="flex items-center justify-between p-2 border rounded hover:bg-muted/50 transition-colors">
                          <div className="flex items-center gap-3">
                            {inj.player.photo && (
                                <img src={inj.player.photo} className="w-8 h-8 rounded-full object-cover" alt={inj.player.name} />
                            )}
                            <div>
                                <div className="font-medium">{inj.player.name}</div>
                                <div className="text-xs text-muted-foreground capitalize">{inj.player.reason}</div>
                            </div>
                          </div>
                          <div className="text-sm font-semibold text-red-500 bg-red-500/10 px-2 py-1 rounded text-xs flex items-center gap-1">
                            <UserX className="w-3 h-3" />
                            {inj.player.type}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
               <div className="text-center p-8 text-muted-foreground">
                 Sakat veya cezalı oyuncu bulunmuyor.
               </div>
            )}
          </CardContent>
        </Card>
      </TabsContent>


      <TabsContent value="predictions" className="space-y-4">
        {predictions && predictions.length > 0 ? (
          <div className="space-y-4">
             {predictions.map((pred: any) => (
                <div key={pred.fixture?.id || 'pred'} className="space-y-6">
                   {/* Winner & Advice */}
                   <Card>
                      <CardHeader>
                         <CardTitle className="text-lg flex items-center gap-2">
                            Winner: <span className="text-primary">{pred.predictions.winner.name}</span>
                         </CardTitle>
                      </CardHeader>
                      <CardContent>
                         <div className="bg-secondary/20 p-4 rounded-md border text-sm">
                            <span className="font-semibold text-muted-foreground block mb-1">Tavsiye:</span>
                            {pred.predictions.advice}
                         </div>
                      </CardContent>
                   </Card>

                   {/* Probabilities */}
                   <Card>
                      <CardHeader>
                         <CardTitle className="text-base">Kazanma İhtimalleri</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                         {/* Home */}
                         <div className="space-y-1">
                            <div className="flex justify-between text-sm">
                               <span>{pred.teams.home.name}</span>
                               <span className="font-bold">{pred.predictions.percent.home}</span>
                            </div>
                            <div className="h-2 bg-secondary rounded-full overflow-hidden">
                               <div className="h-full bg-primary" style={{ width: pred.predictions.percent.home }}></div>
                            </div>
                         </div>
                         {/* Draw */}
                         <div className="space-y-1">
                            <div className="flex justify-between text-sm">
                               <span>Beraberlik</span>
                               <span className="font-bold">{pred.predictions.percent.draw}</span>
                            </div>
                            <div className="h-2 bg-secondary rounded-full overflow-hidden">
                               <div className="h-full bg-yellow-500" style={{ width: pred.predictions.percent.draw }}></div>
                            </div>
                         </div>
                         {/* Away */}
                         <div className="space-y-1">
                            <div className="flex justify-between text-sm">
                               <span>{pred.teams.away.name}</span>
                               <span className="font-bold">{pred.predictions.percent.away}</span>
                            </div>
                            <div className="h-2 bg-secondary rounded-full overflow-hidden">
                               <div className="h-full bg-red-500" style={{ width: pred.predictions.percent.away }}></div>
                            </div>
                         </div>
                      </CardContent>
                   </Card>
                </div>
             ))}
          </div>
        ) : (
          <Card>
            <CardContent className="p-8 text-center text-muted-foreground">
               Tahmin verisi bulunamadı.
            </CardContent>
          </Card>
        )}
      </TabsContent>
    </Tabs>
  )
}
