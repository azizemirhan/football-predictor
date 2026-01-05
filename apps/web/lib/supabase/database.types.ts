export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      leagues: {
        Row: {
          id: number
          name: string
          country: string
          external_id: string | null
          logo_url: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: number
          name: string
          country: string
          external_id?: string | null
          logo_url?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: number
          name?: string
          country?: string
          external_id?: string | null
          logo_url?: string | null
          created_at?: string
          updated_at?: string
        }
      }
      teams: {
        Row: {
          id: number
          name: string
          short_name: string | null
          league_id: number | null
          logo_url: string | null
          elo_rating: number
          attack_strength: number
          defense_strength: number
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: number
          name: string
          short_name?: string | null
          league_id?: number | null
          logo_url?: string | null
          elo_rating?: number
          attack_strength?: number
          defense_strength?: number
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: number
          name?: string
          short_name?: string | null
          league_id?: number | null
          logo_url?: string | null
          elo_rating?: number
          attack_strength?: number
          defense_strength?: number
          created_at?: string
          updated_at?: string
        }
      }
      matches: {
        Row: {
          id: number
          home_team_id: number
          away_team_id: number
          league_id: number
          match_date: string
          home_score: number | null
          away_score: number | null
          status: 'scheduled' | 'live' | 'finished' | 'postponed' | 'cancelled'
          venue: string | null
          external_id: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: number
          home_team_id: number
          away_team_id: number
          league_id: number
          match_date: string
          home_score?: number | null
          away_score?: number | null
          status?: 'scheduled' | 'live' | 'finished' | 'postponed' | 'cancelled'
          venue?: string | null
          external_id?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: number
          home_team_id?: number
          away_team_id?: number
          league_id?: number
          match_date?: string
          home_score?: number | null
          away_score?: number | null
          status?: 'scheduled' | 'live' | 'finished' | 'postponed' | 'cancelled'
          venue?: string | null
          external_id?: string | null
          created_at?: string
          updated_at?: string
        }
      }
      predictions: {
        Row: {
          id: number
          match_id: number
          model_name: string
          home_win_prob: number
          draw_prob: number
          away_win_prob: number
          confidence: number
          created_at: string
        }
        Insert: {
          id?: number
          match_id: number
          model_name: string
          home_win_prob: number
          draw_prob: number
          away_win_prob: number
          confidence?: number
          created_at?: string
        }
        Update: {
          id?: number
          match_id?: number
          model_name?: string
          home_win_prob?: number
          draw_prob?: number
          away_win_prob?: number
          confidence?: number
          created_at?: string
        }
      }
      odds: {
        Row: {
          id: number
          match_id: number
          bookmaker: string
          market_type: string
          home_odds: number | null
          draw_odds: number | null
          away_odds: number | null
          recorded_at: string
        }
        Insert: {
          id?: number
          match_id: number
          bookmaker: string
          market_type: string
          home_odds?: number | null
          draw_odds?: number | null
          away_odds?: number | null
          recorded_at?: string
        }
        Update: {
          id?: number
          match_id?: number
          bookmaker?: string
          market_type?: string
          home_odds?: number | null
          draw_odds?: number | null
          away_odds?: number | null
          recorded_at?: string
        }
      }
      value_bets: {
        Row: {
          id: number
          match_id: number
          prediction_id: number
          selection: string
          predicted_prob: number
          market_odds: number
          edge: number
          kelly_stake: number
          result: 'pending' | 'won' | 'lost' | 'void'
          created_at: string
        }
        Insert: {
          id?: number
          match_id: number
          prediction_id: number
          selection: string
          predicted_prob: number
          market_odds: number
          edge: number
          kelly_stake?: number
          result?: 'pending' | 'won' | 'lost' | 'void'
          created_at?: string
        }
        Update: {
          id?: number
          match_id?: number
          prediction_id?: number
          selection?: string
          predicted_prob?: number
          market_odds?: number
          edge?: number
          kelly_stake?: number
          result?: 'pending' | 'won' | 'lost' | 'void'
          created_at?: string
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      match_status: 'scheduled' | 'live' | 'finished' | 'postponed' | 'cancelled'
      bet_result: 'pending' | 'won' | 'lost' | 'void'
    }
  }
}

// Helper types
export type League = Database['public']['Tables']['leagues']['Row']
export type Team = Database['public']['Tables']['teams']['Row']
export type Match = Database['public']['Tables']['matches']['Row']
export type Prediction = Database['public']['Tables']['predictions']['Row']
export type Odds = Database['public']['Tables']['odds']['Row']
export type ValueBet = Database['public']['Tables']['value_bets']['Row']
