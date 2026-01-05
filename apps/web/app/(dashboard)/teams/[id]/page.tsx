'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowLeft, Users, TrendingUp, ArrowRightLeft, Trophy, Info } from 'lucide-react'
import Link from 'next/link'

interface Player {
  jerseyNumber?: string
  name: string
  position: string
  birthDate?: string
  age: number | null
  nationality: string
  height?: string
  foot?: string
  joinedDate?: string
  contractEnd?: string
  previousClub?: string
  marketValue: string
  profileUrl: string
  imageUrl?: string
}

interface PlayerStat {
  name: string
  position: string
  goals?: number
  assists?: number
  imageUrl?: string
}

interface Transfer {
  playerName: string
  position: string
  age?: number
  nationality?: string
  fromClub?: string
  toClub?: string
  fee: string
  type: 'in' | 'out'
  season?: string
}

interface ClubInfo {
  officialName: string
  address: string
  phone: string
  website: string
  founded: string
  stadium: string
  stadiumCapacity: string
  squadSize: number
  averageAge: string
  foreigners: number
  nationalPlayers: number
  totalMarketValue: string
  leagueRank: string
  coachName: string
  honours: { name: string; count: number }[]
}

interface SofascoreTransfer {
  player: { name: string; slug: string };
  transferFrom?: { name: string; slug: string };
  transferTo?: { name: string; slug: string };
  type?: number; // 1: in, 2: out, 3: loan
  transferFee?: number;
  transferFeeDescription?: string;
  transferDateTimestamp?: number;
}

interface SofascoreFixture {
  id: number;
  slug: string;
  tournament: { name: string; slug: string };
  homeTeam: { name: string; score?: number };
  awayTeam: { name: string; score?: number };
  startTimestamp: number;
  status: { type: string; description: string };
  winnerCode?: number;
}

interface SofascoreStandings {
  position: number;
  matches: number;
  wins: number;
  draws: number;
  losses: number;
  scoresFor: number;
  scoresAgainst: number;
  points: number;
  scoreDiffFormatted: string;
  promotion?: { text: string; id: number };
}

interface SofascoreStatistics {
  rating: string;
  matches: number;
  goalsScored: number;
  goalsConceded: number;
  assists: number;
  possession: string;
  
  // Attack
  shotsOnTarget: number;
  shotsOffTarget: number;
  goalsFromInsideTheBox: number;
  goalsFromOutsideTheBox: number;
  headedGoals: number;
  leftFootGoals: number;
  rightFootGoals: number;
  penaltyGoals: number;
  penaltiesTaken: number;
  hitWoodwork: number;
  
  // Passing
  accuratePasses: number;
  accuratePassesPercentage: number;
  accurateOwnHalfPasses: number;
  accurateOppositionHalfPasses: number;
  accurateLongBallsPercentage: number;
  accurateCrossesPercentage: number;

  // Defence
  cleanSheets: number;
  tackles: number;
  interceptions: number;
  clearances: number;
  errorsLeadingToGoal: number;
  penaltiesCommited: number;

  // Other
  duelsWonPercentage: number;
  aerialDuelsWonPercentage: number;
  possessionLost: number;
  fouls: number;
  yellowCards: number;
  redCards: number;
}

interface SofascorePlayer {
  id: number;
  name: string;
  slug: string;
  position: string;
  jerseyNumber?: string;
  height?: string;
  preferredFoot?: string;
  dateOfBirthTimestamp?: number;
  userCount?: number;
  rating?: string;
  marketValue?: string;
  country?: { alpha2?: string; name?: string };
}

interface SofascoreTeamData {
  id: string;
  name: string;
  fullName?: string;
  manager?: { name: string; id?: number };
  stadium?: { name: string; capacity?: number };
  country?: { name: string };
  category?: { name: string; slug: string };
  tournament?: { name: string; slug: string };
  
  rating?: string;
  statistics?: SofascoreStatistics;
  standings?: SofascoreStandings;
  form?: string[];
  
  squad: SofascorePlayer[];
  transfers?: {
    in: SofascoreTransfer[];
    out: SofascoreTransfer[];
  };
  fixtures?: {
    last: SofascoreFixture[];
    next: SofascoreFixture[];
  };
}

interface TeamData {
  id: number
  name: string
  shortName: string
  logo: string
  league: string
  clubInfo?: ClubInfo
  sofascore?: SofascoreTeamData
  squad: Player[]
  topScorers: PlayerStat[]
  topAssists: PlayerStat[]
  transfers: {
    arrivals: Transfer[]
    departures: Transfer[]
    balance?: {
      income: string
      expenditure: string
      balance: string
    }
  }
  _source: string
}

export default function TeamPage() {
  const params = useParams()
  const teamId = params.id as string
  const [team, setTeam] = useState<TeamData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchTeam() {
      try {
        const res = await fetch(`/api/team/${teamId}`)
        if (!res.ok) throw new Error('Team not found')
        const data = await res.json()
        setTeam(data)
      } catch (e) {
        setError(String(e))
      } finally {
        setLoading(false)
      }
    }
    fetchTeam()
  }, [teamId])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-emerald-500"></div>
      </div>
    )
  }

  if (error || !team) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="p-8 text-center">
          <h2 className="text-xl font-bold text-red-500">Takım Bulunamadı</h2>
          <p className="text-muted-foreground mt-2">{error}</p>
          <Link href="/matches" className="mt-4 inline-block text-emerald-500 hover:underline">
            ← Maçlara Dön
          </Link>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Back Button */}
      <Link href="/matches" className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors">
        <ArrowLeft className="w-4 h-4" />
        Maçlara Dön
      </Link>

      {/* Team Header */}
      <Card className="overflow-hidden">
        <div className="bg-gradient-to-r from-emerald-600 to-emerald-800 p-6">
          <div className="flex items-center gap-6">
            {team.logo && (
              <img 
                src={team.logo} 
                alt={team.name} 
                className="w-24 h-24 object-contain bg-white rounded-lg p-2"
              />
            )}
            <div>
              <h1 className="text-3xl font-bold text-white">{team.name}</h1>
              <p className="text-emerald-100 mt-1">{team.league}</p>
              <div className="flex gap-4 mt-3 text-sm text-emerald-100">
                <span className="flex items-center gap-1">
                  <Users className="w-4 h-4" />
                  {team.squad.length} Oyuncu
                </span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="club" className="w-full">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="club" className="flex items-center gap-2">
            <Info className="w-4 h-4" />
            Kulüp
          </TabsTrigger>
          <TabsTrigger value="sofascore" className="flex items-center gap-2 text-blue-600 data-[state=active]:text-blue-700 data-[state=active]:bg-blue-50">
            <TrendingUp className="w-4 h-4" />
            Sofascore
          </TabsTrigger>
          <TabsTrigger value="squad" className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            Kadro
          </TabsTrigger>
          <TabsTrigger value="stats" className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            İstatistikler
          </TabsTrigger>
          <TabsTrigger value="transfers" className="flex items-center gap-2">
            <ArrowRightLeft className="w-4 h-4" />
            Transferler
          </TabsTrigger>
          <TabsTrigger value="values" className="flex items-center gap-2">
            <Trophy className="w-4 h-4" />
            Değerler
          </TabsTrigger>
        </TabsList>

        {/* Club Info Tab */}
        <TabsContent value="club" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* General Info */}
            <Card>
              <CardHeader className="bg-emerald-500/10 border-b py-3">
                <CardTitle className="text-lg text-emerald-600 flex items-center gap-2">
                  <Info className="w-4 h-4" />
                  Genel Bilgiler
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-3">
                <div className="flex justify-between border-b pb-2">
                  <span className="text-muted-foreground">Resmi Adı</span>
                  <span className="font-medium text-right">{team.clubInfo?.officialName || team.name}</span>
                </div>
                <div className="flex justify-between border-b pb-2">
                  <span className="text-muted-foreground">Kuruluş</span>
                  <span className="font-medium">{team.clubInfo?.founded || '-'}</span>
                </div>
                <div className="flex justify-between border-b pb-2">
                  <span className="text-muted-foreground">Adres</span>
                  <span className="font-medium text-right max-w-[200px] text-xs">{team.clubInfo?.address || '-'}</span>
                </div>
                <div className="flex justify-between border-b pb-2">
                  <span className="text-muted-foreground">Telefon</span>
                  <span className="font-medium">{team.clubInfo?.phone || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Web Sitesi</span>
                  {team.clubInfo?.website ? (
                     <a href={team.clubInfo.website} target="_blank" rel="noreferrer" className="text-emerald-500 hover:underline">
                       {team.clubInfo.website.replace('http://', '').replace('https://', '').split('/')[0]}
                     </a>
                  ) : <span>-</span>}
                </div>
              </CardContent>
            </Card>

            {/* Stadium & Stats */}
            <div className="space-y-4">
              <Card>
                <CardHeader className="bg-blue-500/10 border-b py-3">
                  <CardTitle className="text-lg text-blue-600 flex items-center gap-2">
                    🏟️ Stadyum
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-4 space-y-3">
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-muted-foreground">İsim</span>
                    <span className="font-medium">{team.clubInfo?.stadium || '-'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Kapasite</span>
                    <span className="font-medium">{team.clubInfo?.stadiumCapacity || '-'}</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="bg-purple-500/10 border-b py-3">
                  <CardTitle className="text-lg text-purple-600 flex items-center gap-2">
                    📊 Kulüp Verileri
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-4 space-y-3">
                   <div className="flex justify-between border-b pb-2">
                    <span className="text-muted-foreground">Lig Sıralaması</span>
                    <span className="font-medium">{team.clubInfo?.leagueRank || '-'}</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-muted-foreground">Teknik Direktör</span>
                    <span className="font-medium">{team.clubInfo?.coachName || '-'}</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-muted-foreground">Kadro Genişliği</span>
                    <span className="font-medium">{team.clubInfo?.squadSize || '-'}</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-muted-foreground">Yaş Ortalaması</span>
                    <span className="font-medium">{team.clubInfo?.averageAge || '-'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Yabancı Oyuncular</span>
                    <span className="font-medium">{team.clubInfo?.foreigners || '-'}</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Honours */}
          {team.clubInfo?.honours && team.clubInfo.honours.length > 0 && (
            <Card>
              <CardHeader className="bg-amber-500/10 border-b py-3">
                <CardTitle className="text-lg text-amber-600 flex items-center gap-2">
                  🏆 Başarılar
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                  {team.clubInfo.honours.map((honour, idx) => (
                    <div key={idx} className="flex items-center gap-3 p-3 bg-amber-500/5 rounded-lg border border-amber-100">
                      <div className="bg-amber-100 text-amber-700 font-bold rounded-full w-8 h-8 flex items-center justify-center shrink-0">
                        {honour.count}x
                      </div>
                      <div className="font-medium text-amber-900 leading-tight">
                        {honour.name}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Squad Tab */}
        <TabsContent value="squad" className="space-y-4">
          {team.squad.length === 0 ? (
            <Card className="p-8 text-center text-muted-foreground">
              Kadro bilgisi yükleniyor veya bulunamadı...
            </Card>
          ) : (
            <Card>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-muted/50">
                      <tr>
                        <th className="text-center p-3 font-medium w-12">#</th>
                        <th className="text-left p-3 font-medium">Oyuncu</th>
                        <th className="text-center p-3 font-medium">Yaş</th>
                        <th className="text-left p-3 font-medium">Uyruk</th>
                        <th className="text-center p-3 font-medium">Boy</th>
                        <th className="text-center p-3 font-medium">Ayak</th>
                        <th className="text-left p-3 font-medium">Sözleşme</th>
                        <th className="text-right p-3 font-medium">Piyasa Değeri</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {team.squad.map((player, idx) => (
                        <tr key={idx} className="hover:bg-muted/30 transition-colors">
                          <td className="p-3 text-center font-bold text-muted-foreground">{player.jerseyNumber || idx + 1}</td>
                          <td className="p-3">
                            <div className="flex items-center gap-3">
                              {player.imageUrl && (
                                <img 
                                  src={player.imageUrl} 
                                  alt={player.name}
                                  className="w-10 h-10 rounded-full object-cover"
                                />
                              )}
                              <div>
                                <a 
                                  href={player.profileUrl} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="font-medium hover:text-emerald-500 transition-colors"
                                >
                                  {player.name}
                                </a>
                                {player.position && (
                                  <div className="text-xs text-muted-foreground">{player.position}</div>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="p-3 text-center">{player.age || '-'}</td>
                          <td className="p-3 text-muted-foreground">{player.nationality || '-'}</td>
                          <td className="p-3 text-center text-muted-foreground">{player.height || '-'}</td>
                          <td className="p-3 text-center text-muted-foreground">{player.foot || '-'}</td>
                          <td className="p-3 text-muted-foreground text-xs">{player.contractEnd || '-'}</td>
                          <td className="p-3 text-right font-medium text-emerald-500">{player.marketValue || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Sofascore Tab */}
        <TabsContent value="sofascore" className="space-y-6">
          {!team.sofascore ? (
            <Card className="p-8 text-center text-muted-foreground">
              <div className="flex flex-col items-center gap-2">
                <Info className="w-8 h-8 text-emerald-500/50" />
                <p>Sofascore verisi bulunamadı veya yüklenemedi.</p>
              </div>
            </Card>
          ) : (
            <div className="space-y-6">
              {/* 1. Header Section */}
              <Card className="bg-gradient-to-r from-slate-900 to-slate-800 text-white border-none">
                <CardContent className="p-6">
                  <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                      <h2 className="text-2xl font-bold flex items-center gap-2">
                        {team.sofascore.name}
                        {team.sofascore.country?.name && (
                           <span className="text-sm font-normal px-2 py-0.5 rounded bg-white/10 text-slate-200">
                             {team.sofascore.country.name}
                           </span>
                        )}
                      </h2>
                      <div className="flex gap-4 mt-2 text-sm text-slate-300">
                        {team.sofascore.manager && (
                           <div className="flex items-center gap-1">
                             <Users className="w-4 h-4" />
                             Menajer: <span className="text-white font-medium">{team.sofascore.manager.name}</span>
                           </div>
                        )}
                        {team.sofascore.stadium && (
                           <div className="flex items-center gap-1">
                             🏟️ {team.sofascore.stadium.name} 
                             {team.sofascore.stadium.capacity && <span className="opacity-70">({team.sofascore.stadium.capacity})</span>}
                           </div>
                        )}
                      </div>
                    </div>
                    {team.sofascore.rating && team.sofascore.rating !== '-' && (
                      <div className="bg-blue-600/20 backdrop-blur-sm p-3 rounded-lg border border-blue-500/30 text-center">
                        <div className="text-xs text-blue-200 uppercase tracking-wider mb-1">Sofascore Reyting</div>
                        <div className="text-3xl font-bold text-white">{team.sofascore.rating}</div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Sofascore Sub-Tabs */}
              <Tabs defaultValue="stats" className="w-full">
                <TabsList className="bg-slate-100 p-1 rounded-lg w-full flex justify-start overflow-x-auto">
                    <TabsTrigger value="standings">Puan Durumu</TabsTrigger>
                    <TabsTrigger value="stats">İstatistikler</TabsTrigger>
                    <TabsTrigger value="transfers">Transferler</TabsTrigger>
                    <TabsTrigger value="players">Oyuncular</TabsTrigger>
                    <TabsTrigger value="fixtures">Fikstür</TabsTrigger>
                </TabsList>

                {/* 2. Puan Durumu Tab - Full League Table */}
                <TabsContent value="standings" className="mt-4">
                  <Card>
                    <CardHeader><CardTitle>Puan Durumu</CardTitle></CardHeader>
                    <CardContent className="p-0">
                       {team.sofascore.fullStandings && team.sofascore.fullStandings.length > 0 ? (
                         <div className="overflow-x-auto">
                           <table className="w-full text-sm">
                             <thead className="bg-muted/50 sticky top-0">
                               <tr>
                                 <th className="p-3 text-center w-12">#</th>
                                 <th className="p-3 text-left">Takım</th>
                                 <th className="p-3 text-center">O</th>
                                 <th className="p-3 text-center">G</th>
                                 <th className="p-3 text-center">B</th>
                                 <th className="p-3 text-center">M</th>
                                 <th className="p-3 text-center">AG</th>
                                 <th className="p-3 text-center">YG</th>
                                 <th className="p-3 text-center">Av</th>
                                 <th className="p-3 text-center font-bold">P</th>
                               </tr>
                             </thead>
                             <tbody className="divide-y">
                               {team.sofascore.fullStandings.map((row, idx) => {
                                 const isCurrentTeam = row.teamId?.toString() === team.sofascore.id.toString();
                                 const promotionColor = row.promotion?.id === 804 ? 'border-l-blue-500' :
                                                       row.promotion?.id === 803 ? 'border-l-green-500' :
                                                       row.promotion?.id === 806 ? 'border-l-orange-500' :
                                                       row.promotion?.id === 805 ? 'border-l-red-500' : '';

                                 return (
                                   <tr key={idx} className={`
                                     ${isCurrentTeam ? 'bg-emerald-500/10 font-semibold' : 'hover:bg-muted/30'}
                                     ${promotionColor ? `border-l-4 ${promotionColor}` : ''}
                                     transition-colors
                                   `}>
                                     <td className="p-3 text-center font-medium">{row.position}</td>
                                     <td className="p-3">{row.teamName}</td>
                                     <td className="p-3 text-center">{row.matches}</td>
                                     <td className="p-3 text-center text-green-600">{row.wins}</td>
                                     <td className="p-3 text-center text-muted-foreground">{row.draws}</td>
                                     <td className="p-3 text-center text-red-600">{row.losses}</td>
                                     <td className="p-3 text-center">{row.scoresFor}</td>
                                     <td className="p-3 text-center">{row.scoresAgainst}</td>
                                     <td className="p-3 text-center font-medium">{row.scoreDiffFormatted}</td>
                                     <td className="p-3 text-center font-bold text-lg">{row.points}</td>
                                   </tr>
                                 );
                               })}
                             </tbody>
                           </table>
                         </div>
                       ) : <p className="text-muted-foreground p-4">Puan durumu verisi bulunamadı.</p>}
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* 3. İstatistikler Tab */}
                <TabsContent value="stats" className="mt-4 space-y-6">
                   {!team.sofascore.statistics ? <p>İstatistik bulunamadı.</p> : (
                     <>
                        {/* A. Özet */}
                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                           <Card className="bg-muted/50"><CardContent className="p-4 text-center"><div className="text-muted-foreground text-sm">Reyting</div><div className="text-2xl font-bold text-blue-600">{team.sofascore.rating}</div></CardContent></Card>
                           <Card className="bg-muted/50"><CardContent className="p-4 text-center"><div className="text-muted-foreground text-sm">Gol</div><div className="text-2xl font-bold text-green-600">{team.sofascore.statistics.goalsScored}</div></CardContent></Card>
                           <Card className="bg-muted/50"><CardContent className="p-4 text-center"><div className="text-muted-foreground text-sm">Yenen Gol</div><div className="text-2xl font-bold text-red-600">{team.sofascore.statistics.goalsConceded}</div></CardContent></Card>
                           <Card className="bg-muted/50"><CardContent className="p-4 text-center"><div className="text-muted-foreground text-sm">Asist</div><div className="text-2xl font-bold text-purple-600">{team.sofascore.statistics.assists}</div></CardContent></Card>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                           {/* B. Hücum */}
                           <Card>
                             <CardHeader className="bg-red-50 py-3"><CardTitle className="text-base text-red-700">⚔️ Hücum</CardTitle></CardHeader>
                             <CardContent className="pt-4 space-y-2 text-sm">
                               <div className="flex justify-between border-b pb-1"><span>Maç Başına Gol</span><span className="font-semibold">{(team.sofascore.statistics.goalsScored / team.sofascore.statistics.matches).toFixed(1)}</span></div>
                               <div className="flex justify-between border-b pb-1"><span>Ceza Sahası İçinden Gol</span><span className="font-semibold">{team.sofascore.statistics.goalsFromInsideTheBox}</span></div>
                               <div className="flex justify-between border-b pb-1"><span>Ceza Sahası Dışından Gol</span><span className="font-semibold">{team.sofascore.statistics.goalsFromOutsideTheBox}</span></div>
                               <div className="flex justify-between border-b pb-1"><span>Sol Ayak Gol</span><span className="font-semibold">{team.sofascore.statistics.leftFootGoals}</span></div>
                               <div className="flex justify-between border-b pb-1"><span>Sağ Ayak Gol</span><span className="font-semibold">{team.sofascore.statistics.rightFootGoals}</span></div>
                               <div className="flex justify-between border-b pb-1"><span>Kafa Golü</span><span className="font-semibold">{team.sofascore.statistics.headedGoals}</span></div>
                               <div className="flex justify-between"><span>İsabetli Şut (M.B)</span><span className="font-semibold">{(team.sofascore.statistics.shotsOnTarget / team.sofascore.statistics.matches).toFixed(1)}</span></div>
                             </CardContent>
                           </Card>

                           {/* C. Pas */}
                           <Card>
                             <CardHeader className="bg-blue-50 py-3"><CardTitle className="text-base text-blue-700">⚽ Pas & Topla Oynama</CardTitle></CardHeader>
                             <CardContent className="pt-4 space-y-2 text-sm">
                               <div className="flex justify-between border-b pb-1"><span>Topla Oynama</span><span className="font-semibold">{team.sofascore.statistics.possession}</span></div>
                               <div className="flex justify-between border-b pb-1"><span>İsabetli Pas %</span><span className="font-semibold">{team.sofascore.statistics.accuratePassesPercentage}%</span></div>
                               <div className="flex justify-between border-b pb-1"><span>Kendi Yarı Sahasında Pas</span><span className="font-semibold">{team.sofascore.statistics.accurateOwnHalfPasses}</span></div>
                               <div className="flex justify-between border-b pb-1"><span>Rakip Yarı Sahada Pas</span><span className="font-semibold">{team.sofascore.statistics.accurateOppositionHalfPasses}</span></div>
                               <div className="flex justify-between border-b pb-1"><span>Uzun Top İsabet %</span><span className="font-semibold">{team.sofascore.statistics.accurateLongBallsPercentage}%</span></div>
                               <div className="flex justify-between"><span>Orta İsabet %</span><span className="font-semibold">{team.sofascore.statistics.accurateCrossesPercentage}%</span></div>
                             </CardContent>
                           </Card>

                           {/* D. Savunma */}
                           <Card>
                             <CardHeader className="bg-green-50 py-3"><CardTitle className="text-base text-green-700">🛡️ Savunma</CardTitle></CardHeader>
                             <CardContent className="pt-4 space-y-2 text-sm">
                               <div className="flex justify-between border-b pb-1"><span>Gol Yemediği Maç (Clean Sheet)</span><span className="font-bold text-emerald-600">{team.sofascore.statistics.cleanSheets}</span></div>
                               <div className="flex justify-between border-b pb-1"><span>Maç Başına Yenen Gol</span><span className="font-semibold">{(team.sofascore.statistics.goalsConceded / team.sofascore.statistics.matches).toFixed(1)}</span></div>
                               <div className="flex justify-between border-b pb-1"><span>Maç Başına Top Çalma</span><span className="font-semibold">{(team.sofascore.statistics.tackles / team.sofascore.statistics.matches).toFixed(1)}</span></div>
                               <div className="flex justify-between border-b pb-1"><span>Maç Başına Pas Arası</span><span className="font-semibold">{(team.sofascore.statistics.interceptions / team.sofascore.statistics.matches).toFixed(1)}</span></div>
                               <div className="flex justify-between border-b pb-1"><span>Maç Başına Uzaklaştırma</span><span className="font-semibold">{(team.sofascore.statistics.clearances / team.sofascore.statistics.matches).toFixed(1)}</span></div>
                               <div className="flex justify-between"><span>Penaltıya Sebebiyet</span><span className="font-semibold">{team.sofascore.statistics.penaltiesCommited}</span></div>
                             </CardContent>
                           </Card>

                           {/* E. Diğer */}
                           <Card>
                             <CardHeader className="bg-muted/30 py-3"><CardTitle className="text-base">⚖️ Disiplin & Mücadele</CardTitle></CardHeader>
                             <CardContent className="pt-4 space-y-2 text-sm">
                               <div className="flex justify-between border-b pb-1"><span>İkili Mücadele Kazanma %</span><span className="font-semibold">{team.sofascore.statistics.duelsWonPercentage}%</span></div>
                               <div className="flex justify-between border-b pb-1"><span>Hava Topu Kazanma %</span><span className="font-semibold">{team.sofascore.statistics.aerialDuelsWonPercentage}%</span></div>
                               <div className="flex justify-between border-b pb-1"><span>Top Kaybı (M.B)</span><span className="font-semibold">{(team.sofascore.statistics.possessionLost / team.sofascore.statistics.matches).toFixed(1)}</span></div>
                               <div className="flex justify-between border-b pb-1"><span>Faul (M.B)</span><span className="font-semibold">{(team.sofascore.statistics.fouls / team.sofascore.statistics.matches).toFixed(1)}</span></div>
                               <div className="flex justify-between">
                                  <span>Kartlar</span>
                                  <div className="flex gap-2">
                                     <span className="flex items-center gap-1"><div className="w-3 h-4 bg-yellow-400 rounded-sm"></div> {team.sofascore.statistics.yellowCards}</span>
                                     <span className="flex items-center gap-1"><div className="w-3 h-4 bg-red-600 rounded-sm"></div> {team.sofascore.statistics.redCards}</span>
                                  </div>
                               </div>
                             </CardContent>
                           </Card>
                        </div>
                     </>
                   )}
                </TabsContent>

                {/* 4. Transferler Tab */}
                <TabsContent value="transfers" className="mt-4">
                  {team.sofascore.transfers ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Arrivals */}
                      <Card>
                        <CardHeader className="bg-emerald-50 py-2"><CardTitle className="text-base text-emerald-700">Gelener</CardTitle></CardHeader>
                        <CardContent className="p-0">
                          <div className="max-h-[400px] overflow-y-auto">
                            <table className="w-full text-xs">
                              <tbody className="divide-y">
                                {team.sofascore.transfers.in.map((t, i) => (
                                  <tr key={i} className="hover:bg-slate-50">
                                    <td className="p-2 font-medium">{t.player.name}</td>
                                    <td className="p-2 text-muted-foreground">{t.fromTeamName || '-'}</td>
                                    <td className="p-2 text-right font-medium text-emerald-600">{t.transferFeeDescription || '-'}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </CardContent>
                      </Card>
                      {/* Departures */}
                      <Card>
                        <CardHeader className="bg-red-50 py-2"><CardTitle className="text-base text-red-700">Gidenler</CardTitle></CardHeader>
                        <CardContent className="p-0">
                           <div className="max-h-[400px] overflow-y-auto">
                            <table className="w-full text-xs">
                              <tbody className="divide-y">
                                {team.sofascore.transfers.out.map((t, i) => (
                                  <tr key={i} className="hover:bg-slate-50">
                                    <td className="p-2 font-medium">{t.player.name}</td>
                                    <td className="p-2 text-muted-foreground">{t.toTeamName || '-'}</td>
                                    <td className="p-2 text-right font-medium text-red-600">{t.transferFeeDescription || '-'}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  ) : <p>Transfer verisi yok.</p>}
                </TabsContent>

                {/* 5. Oyuncular Tab */}
                <TabsContent value="players" className="mt-4">
                  <Card>
                    <CardContent className="p-0">
                      <table className="w-full text-sm">
                        <thead className="bg-slate-100">
                          <tr>
                            <th className="p-3 text-left">Oyuncu</th>
                            <th className="p-3 text-center">Mevki</th>
                            <th className="p-3 text-center">Ülke</th>
                            <th className="p-3 text-center">Yaş</th>
                            <th className="p-3 text-center">Boy</th>
                            <th className="p-3 text-right">Reyting</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y">
                          {team.sofascore.squad.map((p, idx) => {
                             const age = p.dateOfBirthTimestamp ? Math.floor((Date.now() - p.dateOfBirthTimestamp * 1000) / (365.25 * 24 * 60 * 60 * 1000)) : '-';
                             return (
                              <tr key={idx} className="hover:bg-slate-50">
                                <td className="p-3 font-medium">{p.name}</td>
                                <td className="p-3 text-center text-muted-foreground">{p.position}</td>
                                <td className="p-3 text-center text-muted-foreground">{p.country?.alpha2 || '-'}</td>
                                <td className="p-3 text-center">{age}</td>
                                <td className="p-3 text-center text-muted-foreground">{p.height || '-'}</td>
                                <td className="p-3 text-right font-bold text-blue-600">{p.rating}</td>
                              </tr>
                             );
                          })}
                        </tbody>
                      </table>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* 6. Fikstür Tab */}
                <TabsContent value="fixtures" className="mt-4">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Son Maçlar */}
                      {team.sofascore.fixtures?.last && team.sofascore.fixtures.last.length > 0 && (
                        <Card>
                          <CardHeader className="py-3"><CardTitle className="text-base text-slate-500">Son Maçlar ({team.sofascore.fixtures.last.length})</CardTitle></CardHeader>
                          <CardContent className="p-0">
                            <div className="max-h-[600px] overflow-y-auto divide-y">
                              {team.sofascore.fixtures.last.map((match, idx) => (
                                <div key={idx} className="p-3 hover:bg-slate-50 transition-colors">
                                  <div className="flex justify-between items-center text-center gap-2">
                                    <div className="text-sm font-semibold flex-1 text-right">{match.homeTeam.name}</div>
                                    <div className="text-lg font-bold bg-slate-100 px-3 py-1 rounded min-w-[60px]">
                                      {match.homeTeam.score !== undefined ? `${match.homeTeam.score}:${match.awayTeam.score}` : 'vs'}
                                    </div>
                                    <div className="text-sm font-semibold flex-1 text-left">{match.awayTeam.name}</div>
                                  </div>
                                  <div className="flex justify-between items-center mt-2 text-xs text-muted-foreground">
                                    <span>{match.tournament.name}</span>
                                    <span>{new Date(match.startTimestamp * 1000).toLocaleDateString('tr-TR')}</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </CardContent>
                        </Card>
                      )}

                      {/* Gelecek Maçlar */}
                      {team.sofascore.fixtures?.next && team.sofascore.fixtures.next.length > 0 && (
                        <Card>
                          <CardHeader className="py-3"><CardTitle className="text-base text-emerald-600">Gelecek Maçlar ({team.sofascore.fixtures.next.length})</CardTitle></CardHeader>
                          <CardContent className="p-0">
                            <div className="max-h-[600px] overflow-y-auto divide-y">
                              {team.sofascore.fixtures.next.map((match, idx) => (
                                <div key={idx} className="p-3 hover:bg-emerald-50 transition-colors">
                                  <div className="flex justify-between items-center text-center gap-2">
                                    <div className="text-sm font-semibold flex-1 text-right">{match.homeTeam.name}</div>
                                    <div className="text-lg font-bold text-slate-400 px-3 py-1 min-w-[60px]">vs</div>
                                    <div className="text-sm font-semibold flex-1 text-left">{match.awayTeam.name}</div>
                                  </div>
                                  <div className="flex justify-between items-center mt-2 text-xs">
                                    <span className="text-muted-foreground">{match.tournament.name}</span>
                                    <span className="text-emerald-600 font-medium">
                                      {new Date(match.startTimestamp * 1000).toLocaleString('tr-TR', {
                                        day: 'numeric',
                                        month: 'short',
                                        hour: '2-digit',
                                        minute: '2-digit'
                                      })}
                                    </span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </CardContent>
                        </Card>
                      )}
                   </div>
                </TabsContent>
              </Tabs>
            </div>
          )}
        </TabsContent>

        {/* Stats Tab */}
        <TabsContent value="stats" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Top Scorers */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  ⚽ Gol Kralları
                </CardTitle>
              </CardHeader>
              <CardContent>
                {team.topScorers.length === 0 ? (
                  <p className="text-muted-foreground text-center py-4">Veri bulunamadı</p>
                ) : (
                  <div className="space-y-3">
                    {team.topScorers.slice(0, 5).map((player, idx) => (
                      <div key={idx} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-lg font-bold text-muted-foreground w-6">{idx + 1}</span>
                          <span className="font-medium">{player.name}</span>
                        </div>
                        <span className="text-xl font-bold text-emerald-500">{player.goals}</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Top Assists */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  🎯 Asist Liderleri
                </CardTitle>
              </CardHeader>
              <CardContent>
                {team.topAssists.length === 0 ? (
                  <p className="text-muted-foreground text-center py-4">Veri bulunamadı</p>
                ) : (
                  <div className="space-y-3">
                    {team.topAssists.slice(0, 5).map((player, idx) => (
                      <div key={idx} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-lg font-bold text-muted-foreground w-6">{idx + 1}</span>
                          <span className="font-medium">{player.name}</span>
                        </div>
                        <span className="text-xl font-bold text-blue-500">{player.assists}</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Transfers Tab */}
        <TabsContent value="transfers" className="space-y-4">
          {/* Transfer Balance Card */}
          {team.transfers.balance?.balance && (
            <Card className="bg-gradient-to-r from-blue-900/20 to-purple-900/20">
              <CardContent className="p-6 text-center">
                <div className="text-sm text-muted-foreground mb-1">Transfer Bilançosu</div>
                <div className={`text-3xl font-bold ${team.transfers.balance.balance?.includes('-') ? 'text-red-500' : 'text-emerald-500'}`}>
                  {team.transfers.balance.balance}
                </div>
              </CardContent>
            </Card>
          )}
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Arrivals */}
            <Card>
              <CardHeader className="bg-emerald-500/10 border-b py-3">
                <CardTitle className="text-lg flex items-center gap-2 text-emerald-600">
                  ➡️ Gelenler ({team.transfers.arrivals.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                {team.transfers.arrivals.length === 0 ? (
                  <p className="text-muted-foreground text-center py-4">Transfer bilgisi bulunamadı</p>
                ) : (
                  <div className="space-y-2">
                    {team.transfers.arrivals.map((transfer, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2 rounded bg-muted/30">
                        <div className="flex-1">
                          <span className="font-medium">{transfer.playerName}</span>
                          {transfer.fromClub && (
                            <span className="text-xs text-muted-foreground block">← {transfer.fromClub}</span>
                          )}
                        </div>
                        <span className="text-emerald-500 font-medium text-sm">{transfer.fee || 'Bedelsiz'}</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Departures */}
            <Card>
              <CardHeader className="bg-red-500/10 border-b py-3">
                <CardTitle className="text-lg flex items-center gap-2 text-red-600">
                  ⬅️ Gidenler ({team.transfers.departures.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                {team.transfers.departures.length === 0 ? (
                  <p className="text-muted-foreground text-center py-4">Transfer bilgisi bulunamadı</p>
                ) : (
                  <div className="space-y-2">
                    {team.transfers.departures.map((transfer, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2 rounded bg-muted/30">
                        <div className="flex-1">
                          <span className="font-medium">{transfer.playerName}</span>
                          {transfer.toClub && (
                            <span className="text-xs text-muted-foreground block">→ {transfer.toClub}</span>
                          )}
                        </div>
                        <span className="text-red-500 font-medium text-sm">{transfer.fee || 'Bedelsiz'}</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Market Values Tab */}
        <TabsContent value="values" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">En Değerli Oyuncular</CardTitle>
            </CardHeader>
            <CardContent>
              {team.squad.length === 0 ? (
                <p className="text-muted-foreground text-center py-4">Veri bulunamadı</p>
              ) : (
                <div className="space-y-3">
                  {team.squad
                    .filter(p => p.marketValue)
                    .sort((a, b) => {
                      const parseValue = (v: string) => {
                        const num = parseFloat(v.replace(/[^\d.,]/g, '').replace(',', '.'));
                        if (v.includes('mil')) return num * 1000000;
                        if (v.includes('bin')) return num * 1000;
                        return num;
                      };
                      return parseValue(b.marketValue) - parseValue(a.marketValue);
                    })
                    .slice(0, 10)
                    .map((player, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 rounded bg-muted/30">
                        <div className="flex items-center gap-3">
                          <span className="text-lg font-bold text-muted-foreground w-6">{idx + 1}</span>
                          {player.imageUrl && (
                            <img src={player.imageUrl} alt={player.name} className="w-8 h-8 rounded-full" />
                          )}
                          <div>
                            <span className="font-medium">{player.name}</span>
                            <span className="text-sm text-muted-foreground ml-2">{player.position}</span>
                          </div>
                        </div>
                        <span className="text-lg font-bold text-emerald-500">{player.marketValue}</span>
                      </div>
                    ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
