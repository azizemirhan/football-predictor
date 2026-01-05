/**
 * Odds API Client
 * 
 * Supports multiple sources:
 * 1. The Odds API (free tier: 500 requests/month)
 * 2. Manual/Mock odds for Nesine/İddaa simulation
 * 
 * In production, you would scrape Nesine.com using Puppeteer/Playwright
 * or use a paid API service like NosyAPI for Turkish betting odds.
 */

// Types
export interface OddsData {
  matchId: string
  externalId?: string
  bookmaker: string
  homeOdds: number
  drawOdds: number
  awayOdds: number
  recordedAt: string
}

export interface BookmakerOdds {
  key: string
  title: string
  markets: {
    key: string
    outcomes: {
      name: string
      price: number
    }[]
  }[]
}

// The Odds API client (free tier available)
const ODDS_API_KEY = process.env.ODDS_API_KEY || ''
const ODDS_API_BASE = 'https://api.the-odds-api.com/v4'

export async function getOddsFromAPI(sportKey: string = 'soccer_epl'): Promise<OddsData[]> {
  if (!ODDS_API_KEY) {
    console.warn('ODDS_API_KEY not configured, using mock odds')
    return []
  }

  try {
    const url = `${ODDS_API_BASE}/sports/${sportKey}/odds?apiKey=${ODDS_API_KEY}&regions=uk&markets=h2h`
    const response = await fetch(url)
    
    if (!response.ok) {
      console.error('Odds API error:', response.status)
      return []
    }
    
    const data = await response.json()
    const allOdds: OddsData[] = []
    
    for (const match of data) {
      for (const bookmaker of match.bookmakers || []) {
        const h2hMarket = bookmaker.markets?.find((m: any) => m.key === 'h2h')
        if (!h2hMarket) continue
        
        const homeOutcome = h2hMarket.outcomes.find((o: any) => o.name === match.home_team)
        const awayOutcome = h2hMarket.outcomes.find((o: any) => o.name === match.away_team)
        const drawOutcome = h2hMarket.outcomes.find((o: any) => o.name === 'Draw')
        
        if (homeOutcome && awayOutcome && drawOutcome) {
          allOdds.push({
            matchId: match.id,
            externalId: match.id,
            bookmaker: bookmaker.title,
            homeOdds: homeOutcome.price,
            drawOdds: drawOutcome.price,
            awayOdds: awayOutcome.price,
            recordedAt: new Date().toISOString()
          })
        }
      }
    }
    
    return allOdds
  } catch (error) {
    console.error('Failed to fetch odds:', error)
    return []
  }
}

/**
 * Simulated Nesine/İddaa odds generator
 * 
 * In production, this would be replaced with actual scraping logic.
 * For now, we generate realistic odds based on Elo ratings.
 */
export function generateNesineOdds(
  homeElo: number, 
  awayElo: number,
  matchId: string
): OddsData[] {
  // Calculate probabilities from Elo
  const eloDiff = homeElo - awayElo + 100 // Home advantage
  const homeProb = 1 / (1 + Math.pow(10, -eloDiff / 400))
  const drawProb = 0.26 // Average draw probability in football
  const awayProb = 1 - homeProb - drawProb
  
  // Convert probabilities to odds with margin (bookmaker profit ~5-8%)
  const margin = 1.06 // 6% overround
  const homeOdds = roundOdds(margin / Math.max(homeProb, 0.05))
  const drawOdds = roundOdds(margin / drawProb)
  const awayOdds = roundOdds(margin / Math.max(awayProb, 0.05))
  
  const now = new Date().toISOString()
  
  return [
    {
      matchId,
      bookmaker: 'Nesine',
      homeOdds,
      drawOdds,
      awayOdds,
      recordedAt: now
    },
    {
      matchId,
      bookmaker: 'İddaa',
      homeOdds: homeOdds * (0.98 + Math.random() * 0.04), // Slight variation
      drawOdds: drawOdds * (0.98 + Math.random() * 0.04),
      awayOdds: awayOdds * (0.98 + Math.random() * 0.04),
      recordedAt: now
    }
  ]
}

// Helper to round odds to realistic values
function roundOdds(odds: number): number {
  if (odds < 1.5) return Math.round(odds * 100) / 100
  if (odds < 3) return Math.round(odds * 20) / 20
  if (odds < 10) return Math.round(odds * 10) / 10
  return Math.round(odds * 2) / 2
}

/**
 * Calculate value bet opportunities
 * 
 * A value bet exists when our predicted probability is higher
 * than the implied probability from the bookmaker odds.
 */
export function findValueBets(
  predictedHomeProb: number,
  predictedDrawProb: number,
  predictedAwayProb: number,
  odds: OddsData,
  minEdge: number = 0.03 // 3% minimum edge
): {
  selection: 'home' | 'draw' | 'away' | null
  edge: number
  kellyStake: number
} | null {
  // Calculate implied probabilities from odds
  const impliedHome = 1 / odds.homeOdds
  const impliedDraw = 1 / odds.drawOdds
  const impliedAway = 1 / odds.awayOdds
  
  // Calculate edges
  const homeEdge = predictedHomeProb - impliedHome
  const drawEdge = predictedDrawProb - impliedDraw
  const awayEdge = predictedAwayProb - impliedAway
  
  // Find best value bet
  let bestSelection: 'home' | 'draw' | 'away' | null = null
  let bestEdge = 0
  let bestOdds = 0
  let bestProb = 0
  
  if (homeEdge > minEdge && homeEdge > bestEdge) {
    bestSelection = 'home'
    bestEdge = homeEdge
    bestOdds = odds.homeOdds
    bestProb = predictedHomeProb
  }
  
  if (drawEdge > minEdge && drawEdge > bestEdge) {
    bestSelection = 'draw'
    bestEdge = drawEdge
    bestOdds = odds.drawOdds
    bestProb = predictedDrawProb
  }
  
  if (awayEdge > minEdge && awayEdge > bestEdge) {
    bestSelection = 'away'
    bestEdge = awayEdge
    bestOdds = odds.awayOdds
    bestProb = predictedAwayProb
  }
  
  if (!bestSelection) return null
  
  // Calculate Kelly Criterion stake
  // Kelly = (bp - q) / b
  // where b = odds - 1, p = probability of winning, q = 1 - p
  const b = bestOdds - 1
  const p = bestProb
  const q = 1 - p
  const kellyFraction = (b * p - q) / b
  
  // Use fractional Kelly (25%) for safer betting
  const kellyStake = Math.max(0, Math.min(0.1, kellyFraction * 0.25))
  
  return {
    selection: bestSelection,
    edge: bestEdge,
    kellyStake
  }
}
