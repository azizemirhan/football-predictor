/**
 * Football-Data.org API Client
 * Free tier: 10 requests/minute, Premier League data
 * Docs: https://www.football-data.org/documentation/quickstart
 */

const API_BASE = 'https://api.football-data.org/v4'
const API_KEY = process.env.FOOTBALL_DATA_API_KEY || ''

interface ApiResponse<T> {
  data: T | null
  error: string | null
}

// Rate limiting helper
let lastRequestTime = 0
const MIN_REQUEST_INTERVAL = 6100 // 10 requests per minute = 6 seconds between requests

async function rateLimitedFetch(url: string): Promise<Response> {
  const now = Date.now()
  const timeSinceLastRequest = now - lastRequestTime
  
  if (timeSinceLastRequest < MIN_REQUEST_INTERVAL) {
    await new Promise(resolve => setTimeout(resolve, MIN_REQUEST_INTERVAL - timeSinceLastRequest))
  }
  
  lastRequestTime = Date.now()
  
  return fetch(url, {
    headers: {
      'X-Auth-Token': API_KEY,
    },
    next: { revalidate: 300 } // Cache for 5 minutes
  })
}

// Types
export interface Competition {
  id: number
  name: string
  code: string
  emblem: string
  currentSeason: {
    id: number
    startDate: string
    endDate: string
    currentMatchday: number
  }
}

export interface Team {
  id: number
  name: string
  shortName: string
  tla: string
  crest: string
}

export interface Match {
  id: number
  utcDate: string
  status: 'SCHEDULED' | 'TIMED' | 'IN_PLAY' | 'PAUSED' | 'FINISHED' | 'SUSPENDED' | 'POSTPONED' | 'CANCELLED'
  matchday: number
  homeTeam: Team
  awayTeam: Team
  score: {
    winner: string | null
    fullTime: { home: number | null; away: number | null }
    halfTime: { home: number | null; away: number | null }
  }
}

export interface Standing {
  position: number
  team: Team
  playedGames: number
  won: number
  draw: number
  lost: number
  points: number
  goalsFor: number
  goalsAgainst: number
  goalDifference: number
}

// API Functions
export async function getCompetition(code: string = 'PL'): Promise<ApiResponse<Competition>> {
  try {
    const response = await rateLimitedFetch(`${API_BASE}/competitions/${code}`)
    
    if (!response.ok) {
      return { data: null, error: `API Error: ${response.status}` }
    }
    
    const data = await response.json()
    return { data, error: null }
  } catch (error) {
    return { data: null, error: String(error) }
  }
}

export async function getMatches(options: {
  competition?: string
  dateFrom?: string
  dateTo?: string
  status?: string
} = {}): Promise<ApiResponse<Match[]>> {
  try {
    const params = new URLSearchParams()
    if (options.dateFrom) params.append('dateFrom', options.dateFrom)
    if (options.dateTo) params.append('dateTo', options.dateTo)
    if (options.status) params.append('status', options.status)
    
    const competition = options.competition || 'PL'
    const url = `${API_BASE}/competitions/${competition}/matches?${params.toString()}`
    
    const response = await rateLimitedFetch(url)
    
    if (!response.ok) {
      return { data: null, error: `API Error: ${response.status}` }
    }
    
    const data = await response.json()
    return { data: data.matches, error: null }
  } catch (error) {
    return { data: null, error: String(error) }
  }
}

export async function getUpcomingMatches(days: number = 7): Promise<ApiResponse<Match[]>> {
  const today = new Date()
  const futureDate = new Date(today.getTime() + days * 24 * 60 * 60 * 1000)
  
  return getMatches({
    dateFrom: today.toISOString().split('T')[0],
    dateTo: futureDate.toISOString().split('T')[0],
    status: 'SCHEDULED'
  })
}

export async function getStandings(competition: string = 'PL'): Promise<ApiResponse<Standing[]>> {
  try {
    const response = await rateLimitedFetch(`${API_BASE}/competitions/${competition}/standings`)
    
    if (!response.ok) {
      return { data: null, error: `API Error: ${response.status}` }
    }
    
    const data = await response.json()
    // Return total standings
    const standingsTable = data.standings?.find((s: any) => s.type === 'TOTAL')
    return { data: standingsTable?.table || [], error: null }
  } catch (error) {
    return { data: null, error: String(error) }
  }
}

export async function getTeams(competition: string = 'PL'): Promise<ApiResponse<Team[]>> {
  try {
    const response = await rateLimitedFetch(`${API_BASE}/competitions/${competition}/teams`)
    
    if (!response.ok) {
      return { data: null, error: `API Error: ${response.status}` }
    }
    
    const data = await response.json()
    return { data: data.teams, error: null }
  } catch (error) {
    return { data: null, error: String(error) }
  }
}

export async function getMatchById(matchId: number): Promise<ApiResponse<Match>> {
  try {
    const response = await rateLimitedFetch(`${API_BASE}/matches/${matchId}`)
    
    if (!response.ok) {
      return { data: null, error: `API Error: ${response.status}` }
    }
    
    const data = await response.json()
    return { data, error: null }
  } catch (error) {
    return { data: null, error: String(error) }
  }
}
