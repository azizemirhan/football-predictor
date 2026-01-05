
import puppeteer from 'puppeteer';

export interface SofascorePlayer {
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

export interface SofascoreTransfer {
  player: { name: string; slug: string };
  transferFrom?: { name: string; slug: string };
  transferTo?: { name: string; slug: string };
  fromTeamName?: string;
  toTeamName?: string;
  type?: number;
  transferDateTimestamp?: number;
  transferFee?: number;
  transferFeeDescription?: string;
}

export interface SofascoreFixture {
  id: number;
  slug: string;
  tournament: { name: string; slug: string };
  homeTeam: { name: string; score?: number };
  awayTeam: { name: string; score?: number };
  startTimestamp: number;
  status: { type: string; description: string };
  winnerCode?: number; // 1, 2, 3 (draw)
}

export interface SofascoreStandings {
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

export interface SofascoreStatistics {
  // Summary
  rating: string;
  matches: number;
  goalsScored: number;
  goalsConceded: number;
  assists: number;
  
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
  possession: string; // avgBallPossession
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

export interface SofascoreTeamData {
  id: string;
  name: string;
  fullName?: string;
  manager?: { name: string; id?: number };
  stadium?: { name: string; capacity?: number };
  country?: { name: string };
  
  // Categories
  category?: { name: string; slug: string };
  tournament?: { name: string; slug: string };
  
  // Standings
  standings?: SofascoreStandings;
  form?: string[]; // W D L sequence derived from last matches or standings

  // Detailed Stats
  statistics?: SofascoreStatistics;

  // Squad
  squad: SofascorePlayer[];
  
  // Transfers
  transfers?: {
    in: SofascoreTransfer[];
    out: SofascoreTransfer[];
  };

  // Fixtures
  fixtures?: {
    last: SofascoreFixture[];
    next: SofascoreFixture[];
  };
}

const USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';

async function fetchInBrowser(page: any, url: string) {
    return page.evaluate((u: string) => {
        return fetch(u)
            .then(res => {
                if (!res.ok) return { error: res.statusText, status: res.status };
                return res.json();
            })
            .catch(e => ({ error: e.toString() }));
    }, url);
}

export async function getSofascoreId(teamName: string): Promise<string | null> {
  const browser = await puppeteer.launch({ 
    headless: true, 
    args: ['--no-sandbox', '--disable-setuid-sandbox'] 
  });
  
  try {
    const page = await browser.newPage();
    await page.setUserAgent(USER_AGENT);
    
    // Navigate to homepage to get valid session cookies
    await page.goto('https://www.sofascore.com', { waitUntil: 'networkidle2' });

    // Internal API Search
    const searchResult = await fetchInBrowser(page, `https://api.sofascore.com/api/v1/search/all?q=${encodeURIComponent(teamName)}`);

    if (searchResult && searchResult.results && searchResult.results.length > 0) {
        const team = searchResult.results.find((r: any) => r.type === 'team' && r.entity.sport.name === 'Football');
        if (team) {
            return team.entity.id.toString();
        }
    }
    return null;

  } catch (e) {
    console.error(`Error searching Sofascore ID for ${teamName}:`, e);
    return null;
  } finally {
    await browser.close();
  }
}

export async function scrapeSofascoreTeam(teamId: string): Promise<SofascoreTeamData | null> {
  const browser = await puppeteer.launch({ 
    headless: true, 
    args: ['--no-sandbox', '--disable-setuid-sandbox'] 
  });
  
  try {
    const page = await browser.newPage();
    await page.setUserAgent(USER_AGENT);
    
    await page.goto('https://www.sofascore.com', { waitUntil: 'networkidle2' });

    // 1. Team Details
    const teamData = await fetchInBrowser(page, `https://api.sofascore.com/api/v1/team/${teamId}`);
    if (!teamData || teamData.error || !teamData.team) return null;

    const t = teamData.team;
    let stats: SofascoreStatistics | undefined;
    let squad: SofascorePlayer[] = [];
    let transfers: { in: SofascoreTransfer[], out: SofascoreTransfer[] } = { in: [], out: [] };
    let fixtures: { last: SofascoreFixture[], next: SofascoreFixture[] } = { last: [], next: [] };
    let standing: SofascoreStandings | undefined;
    let form: string[] = [];

    // 2. Fetch Players
    const playersData = await fetchInBrowser(page, `https://api.sofascore.com/api/v1/team/${teamId}/players`);
    if (playersData && playersData.players) {
        squad = playersData.players.map((p: any) => ({
            id: p.player.id,
            name: p.player.name,
            slug: p.player.slug,
            position: p.player.position,
            jerseyNumber: p.player.jerseyNumber,
            height: p.player.height,
            dateOfBirthTimestamp: p.player.dateOfBirthTimestamp,
            country: p.player.country,
            rating: '-' // Will be enriched
        }));
    }

    // 3. Fetch Season Data (Stats, Standings, etc.)
    const tournamentId = t.primaryUniqueTournament?.id;
    if (tournamentId) {
        const seasonsData = await fetchInBrowser(page, `https://api.sofascore.com/api/v1/unique-tournament/${tournamentId}/seasons`);
        const currentSeason = seasonsData?.seasons?.[0]; // Usually first is current

        if (currentSeason) {
            // A. Detailed Stats
            const statsData = await fetchInBrowser(page, `https://api.sofascore.com/api/v1/team/${teamId}/unique-tournament/${tournamentId}/season/${currentSeason.id}/statistics/overall`);
            if (statsData?.statistics) {
                const s = statsData.statistics;
                stats = {
                    // Summary
                    rating: s.avgRating ? s.avgRating.toFixed(2) : '-',
                    matches: s.matches || 0,
                    goalsScored: s.goalsScored || 0,
                    goalsConceded: s.goalsConceded || 0,
                    assists: s.assists || 0,
                    // Attack
                    shotsOnTarget: s.shotsOnTarget || 0,
                    shotsOffTarget: s.shotsOffTarget || 0,
                    goalsFromInsideTheBox: s.goalsFromInsideTheBox || 0,
                    goalsFromOutsideTheBox: s.goalsFromOutsideTheBox || 0,
                    headedGoals: s.headedGoals || 0,
                    leftFootGoals: s.leftFootGoals || 0,
                    rightFootGoals: s.rightFootGoals || 0,
                    penaltyGoals: s.penaltyGoals || 0,
                    penaltiesTaken: s.penaltiesTaken || 0,
                    hitWoodwork: s.hitWoodwork || 0,
                    // Passing
                    possession: s.averageBallPossession ? s.averageBallPossession.toFixed(1) + '%' : '0%',
                    accuratePasses: s.accuratePasses || 0,
                    accuratePassesPercentage: s.accuratePassesPercentage || 0,
                    accurateOwnHalfPasses: s.accurateOwnHalfPasses || 0,
                    accurateOppositionHalfPasses: s.accurateOppositionHalfPasses || 0,
                    accurateLongBallsPercentage: s.accurateLongBallsPercentage || 0,
                    accurateCrossesPercentage: s.accurateCrossesPercentage || 0,
                    // Defence
                    cleanSheets: s.cleanSheets || 0,
                    tackles: s.tackles || 0,
                    interceptions: s.interceptions || 0,
                    clearances: s.clearances || 0,
                    errorsLeadingToGoal: s.errorsLeadingToGoal || 0,
                    penaltiesCommited: s.penaltiesCommited || 0,
                    // Other
                    duelsWonPercentage: s.duelsWonPercentage || 0,
                    aerialDuelsWonPercentage: s.aerialDuelsWonPercentage || 0,
                    possessionLost: s.possessionLost || 0,
                    fouls: s.fouls || 0,
                    yellowCards: s.yellowCards || 0,
                    redCards: s.redCards || 0
                };
            }

            // B. Standings & Form
            const standingsData = await fetchInBrowser(page, `https://api.sofascore.com/api/v1/unique-tournament/${tournamentId}/season/${currentSeason.id}/standings/total`);
            if (standingsData?.standings) {
                const table = standingsData.standings[0]?.rows || [];
                const teamRow = table.find((row: any) => row.team.id.toString() === teamId);
                if (teamRow) {
                    standing = {
                        position: teamRow.position,
                        matches: teamRow.matches,
                        wins: teamRow.wins,
                        draws: teamRow.draws,
                        losses: teamRow.losses,
                        scoresFor: teamRow.scoresFor,
                        scoresAgainst: teamRow.scoresAgainst,
                        points: teamRow.points,
                        scoreDiffFormatted: teamRow.scoreDiffFormatted,
                        promotion: teamRow.promotion
                    };
                    
                    // Extract Form from row if available or fetches
                    // Sofascore doesn't always send form in standings, but let's check
                }
            }
            
            // C. Player Ratings
             // C. Player Ratings - Endpoint seems unstable/changed, skipping for now to avoid errors
             // Ideally we would fetch per-player rating but for now we rely on squad data
        }
    }

    // 4. Transfers
    const transfersData = await fetchInBrowser(page, `https://api.sofascore.com/api/v1/team/${teamId}/transfers`);
    if (transfersData) {
        const mapTransfer = (t: any) => ({
            player: { name: t.player.name, slug: t.player.slug },
            transferFrom: t.transferFrom ? { name: t.transferFrom.name, slug: t.transferFrom.slug } : undefined,
            transferTo: t.transferTo ? { name: t.transferTo.name, slug: t.transferTo.slug } : undefined,
            fromTeamName: t.transferFrom?.name,
            toTeamName: t.transferTo?.name,
            type: t.type,
            transferDateTimestamp: t.transferDateTimestamp,
            transferFee: t.transferFeeRaw?.value,
            transferFeeDescription: t.transferFeeDescription
        });

        if (transfersData.transfersIn) transfers.in = transfersData.transfersIn.map(mapTransfer);
        if (transfersData.transfersOut) transfers.out = transfersData.transfersOut.map(mapTransfer);
    }

    // 5. Fixtures (fetch last 20 and next 20 matches)
    const nextData = await fetchInBrowser(page, `https://api.sofascore.com/api/v1/team/${teamId}/events/next/20`);
    const lastData = await fetchInBrowser(page, `https://api.sofascore.com/api/v1/team/${teamId}/events/last/20`);

    const mapFixture = (e: any) => ({
        id: e.id,
        slug: e.slug,
        tournament: { name: e.tournament.name, slug: e.tournament.slug },
        homeTeam: { name: e.homeTeam.name, score: e.homeScore?.current },
        awayTeam: { name: e.awayTeam.name, score: e.awayScore?.current },
        startTimestamp: e.startTimestamp,
        status: { type: e.status.type, description: e.status.description },
        winnerCode: e.winnerCode
    });

    if (nextData?.events) fixtures.next = nextData.events.map(mapFixture);
    if (lastData?.events) fixtures.last = lastData.events.map(mapFixture);

    // Derive Form from last 5 matches
    form = fixtures.last.slice(0, 5).map(f => {
        if (!f.winnerCode) return 'D';
        // Assume I am the teamId. Need to check if I was home or away.
        // Simplified form: W/D/L
        // Logic: if winnerCode is 1 (home) and I am home -> W
        // This requires knowing if I am home or away.
        // Let's rely on winnerCode if possible or score
        return '?';
    });
    // Actually, Sofascore provides form in standings/form endpoint usually
    // api/v1/team/{id}/performance/form/events
    const formData = await fetchInBrowser(page, `https://api.sofascore.com/api/v1/team/${teamId}/performance/form/events`);
    if (formData?.events) {
        // Map form events to W/D/L
        // This endpoint usually gives exact correct form
         form = formData.events.map((e: any) => e.formDisplay); // e.g. "W", "L"
    }

    return {
        id: teamId,
        name: t.name,
        fullName: t.fullName,
        manager: t.manager,
        stadium: t.venue ? { name: t.venue.name, capacity: t.venue.capacity } : undefined,
        country: t.country,
        category: t.category,
        tournament: t.tournament,
        
        standings: standing,
        statistics: stats,
        form: form,
        
        squad: squad,
        transfers: transfers,
        fixtures: fixtures
    };

  } catch (e) {
    console.error('Error scraping Sofascore:', e);
    return null;
  } finally {
    await browser.close();
  }
}
