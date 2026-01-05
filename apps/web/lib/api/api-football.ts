const API_URL = 'https://v3.football.api-sports.io'
const API_KEY = process.env.RAPIDAPI_KEY
const LEAGUE_ID = 39 // Premier League
const SEASON = 2025 // Current season for Jan 2026

if (!API_KEY) {
  console.warn('RAPIDAPI_KEY is not set')
}

export interface ApiFootballTeam {
  team: {
    id: number
    name: string
    code: string
    logo: string
  }
  venue: {
    name: string
    city: string
  }
}

export interface ApiFootballMatch {
  fixture: {
    id: number
    date: string
    status: {
      long: string
      short: string
      elapsed?: number | null // Add elapsed time
    }
    venue: {
      name: string
    }
  }
  teams: {
    home: ApiFootballTeam['team'] & { winner: boolean | null }
    away: ApiFootballTeam['team'] & { winner: boolean | null }
  }
  goals: {
    home: number | null
    away: number | null
  }
  score: {
    fulltime: {
      home: number | null
      away: number | null
    }
  }
}

export interface ApiFootballOdds {
  fixture: {
    id: number
  }
  update: string
  bookmakers: {
    id: number
    name: string
    bets: {
      id: number
      name: string
      values: {
        value: string
        odd: string
      }[]
    }[]
  }[]
}

export async function fetchApi(endpoint: string, params: Record<string, string> = {}) {
  const url = new URL(`${API_URL}/${endpoint}`)
  Object.keys(params).forEach(key => url.searchParams.append(key, params[key]))

  const response = await fetch(url.toString(), {
    headers: {
      'x-apisports-key': API_KEY || '',
    },
    next: { revalidate: 0 }
  })

  if (!response.ok) {
    throw new Error(`API-Football Error: ${response.status} ${response.statusText}`)
  }

  const data = await response.json()
  
  if (data.errors && Object.keys(data.errors).length > 0) {
    console.error('API-Football API Errors:', data.errors)
    throw new Error('API returned errors: ' + JSON.stringify(data.errors))
  }

  return data.response
}

export async function getTeams() {
  return fetchApi('teams', {
    league: String(LEAGUE_ID),
    season: String(SEASON)
  }) as Promise<ApiFootballTeam[]>
}

export async function getFixtures(from: string, to: string) {
  return fetchApi('fixtures', {
    league: String(LEAGUE_ID),
    season: String(SEASON),
    from,
    to
  }) as Promise<ApiFootballMatch[]>
}

export async function getLiveFixtures() {
  return fetchApi('fixtures', {
    league: String(LEAGUE_ID),
    season: String(SEASON),
    live: 'all'
  }) as Promise<ApiFootballMatch[]>
}

export async function getOdds(params: { fixtureId?: number, date?: string, page?: number } = {}) {
  const queryParams: Record<string, string> = {
    league: String(LEAGUE_ID),
    season: String(SEASON),
    bookmaker: '1' // Bet365
  }
  
  if (params.fixtureId) queryParams.fixture = String(params.fixtureId)
  if (params.date) queryParams.date = params.date
  if (params.page) queryParams.page = String(params.page)
  
  return fetchApi('odds', queryParams) as Promise<ApiFootballOdds[]>
}

export async function getStandings() {
  const data = await fetchApi('standings', {
    league: String(LEAGUE_ID),
    season: String(SEASON)
  })
  return data[0]?.league?.standings[0] || []
}

export async function getPredictions(fixtureId: number) {
  return fetchApi('predictions', {
    fixture: String(fixtureId)
  })
}

export async function getTeamStatistics(teamId: number) {
  return fetchApi('teams/statistics', {
    team: String(teamId),
    league: String(LEAGUE_ID),
    season: String(SEASON)
  })
}

export async function getPlayerStats(teamId: number) {
  return fetchApi('players', {
    team: String(teamId),
    league: String(LEAGUE_ID),
    season: String(SEASON)
  })
}
