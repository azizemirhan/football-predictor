"""
LLM Prompts - Sistem ve analiz promptları
"""

from typing import Any, Dict


def get_system_prompt(role: str = "analyst") -> str:
    """Get system prompt for LLM"""
    
    prompts = {
        "analyst": """You are an expert football analyst with deep knowledge of:
- Tactical analysis and team formations
- Statistical modeling and prediction
- Player performance metrics
- League dynamics and historical trends
- Betting markets and value identification

Provide accurate, data-driven analysis. Be specific with numbers and percentages.
When making predictions, clearly state your reasoning and confidence level.
Acknowledge uncertainty when data is limited.""",

        "tactical_analyst": """You are a tactical football analyst specializing in:
- Formation analysis and tactical setups
- Player roles and responsibilities
- Pressing patterns and defensive structures
- Set-piece strategies
- In-game tactical adjustments

Provide detailed tactical insights with specific examples.
Reference relevant historical matches when applicable.""",

        "betting_analyst": """You are a professional betting analyst focused on:
- Value bet identification
- Odds analysis and market inefficiencies
- Bankroll management
- Risk assessment
- Kelly Criterion application

Always quantify edge and recommended stakes.
Be conservative in recommendations and highlight risks clearly.""",

        "news_analyst": """You are a football news analyst who:
- Monitors team news and injury updates
- Analyzes sentiment from media coverage
- Identifies factors that could impact match outcomes
- Tracks manager comments and tactical hints
- Assesses squad morale and internal dynamics

Provide objective, fact-based summaries."""
    }
    
    return prompts.get(role, prompts["analyst"])


def get_match_analysis_prompt(
    home_team: str,
    away_team: str,
    context: Dict[str, Any]
) -> str:
    """Generate match analysis prompt"""
    
    # Build context sections
    sections = []
    
    # Form section
    if context.get("home_form") or context.get("away_form"):
        sections.append(f"""
FORM:
- {home_team}: {context.get('home_form', 'N/A')} (Last 5: {context.get('home_form_string', 'N/A')})
- {away_team}: {context.get('away_form', 'N/A')} (Last 5: {context.get('away_form_string', 'N/A')})
""")
    
    # Statistics section
    if any(k in context for k in ['home_goals_avg', 'home_xg', 'home_possession']):
        sections.append(f"""
STATISTICS:
- {home_team} Goals/Game: {context.get('home_goals_avg', 'N/A')} (xG: {context.get('home_xg', 'N/A')})
- {away_team} Goals/Game: {context.get('away_goals_avg', 'N/A')} (xG: {context.get('away_xg', 'N/A')})
- {home_team} Clean Sheets: {context.get('home_clean_sheets', 'N/A')}
- {away_team} Clean Sheets: {context.get('away_clean_sheets', 'N/A')}
""")
    
    # Ratings section
    if context.get("home_elo") or context.get("home_rating"):
        sections.append(f"""
RATINGS:
- {home_team} Elo: {context.get('home_elo', 'N/A')}
- {away_team} Elo: {context.get('away_elo', 'N/A')}
- Elo Difference: {context.get('elo_diff', 'N/A')}
""")
    
    # H2H section
    if context.get("h2h_home_wins") is not None:
        sections.append(f"""
HEAD-TO-HEAD (Last {context.get('h2h_matches', 10)} meetings):
- {home_team} Wins: {context.get('h2h_home_wins', 'N/A')}
- Draws: {context.get('h2h_draws', 'N/A')}
- {away_team} Wins: {context.get('h2h_away_wins', 'N/A')}
""")
    
    # Model predictions section
    if context.get("model_prediction"):
        pred = context["model_prediction"]
        sections.append(f"""
MODEL PREDICTION:
- Home Win: {pred.get('home_win_prob', 0):.1%}
- Draw: {pred.get('draw_prob', 0):.1%}
- Away Win: {pred.get('away_win_prob', 0):.1%}
- Expected Score: {pred.get('expected_home_goals', '?'):.1f} - {pred.get('expected_away_goals', '?'):.1f}
""")
    
    # Odds section
    if context.get("odds"):
        odds = context["odds"]
        sections.append(f"""
BETTING ODDS:
- Home: {odds.get('home', 'N/A')}
- Draw: {odds.get('draw', 'N/A')}
- Away: {odds.get('away', 'N/A')}
""")
    
    # Injuries section
    if context.get("home_injuries") or context.get("away_injuries"):
        sections.append(f"""
INJURIES/SUSPENSIONS:
- {home_team}: {', '.join(context.get('home_injuries', ['None reported']))}
- {away_team}: {', '.join(context.get('away_injuries', ['None reported']))}
""")
    
    context_text = "\n".join(sections) if sections else "Limited data available."
    
    prompt = f"""Analyze the following Premier League match:

{home_team} vs {away_team}

{context_text}

Provide a comprehensive analysis including:

1. **Prediction**: Your predicted outcome (Home Win / Draw / Away Win) with confidence percentage

2. **Score Prediction**: Most likely scoreline

3. **Key Factors**: Top 3-5 factors influencing your prediction
   - List as bullet points

4. **Risk Factors**: Potential reasons your prediction could be wrong
   - List as bullet points

5. **Value Assessment**: Based on the odds (if provided), is there betting value?

6. **Brief Reasoning**: 2-3 sentences explaining your overall analysis

Be specific with data references. Express confidence as a percentage (e.g., 65%)."""

    return prompt


def get_value_bet_prompt(
    match: Dict,
    prediction: Dict,
    odds: Dict
) -> str:
    """Generate value bet analysis prompt"""
    
    implied_probs = {
        "home": 1 / odds.get("home", 1) if odds.get("home") else 0,
        "draw": 1 / odds.get("draw", 1) if odds.get("draw") else 0,
        "away": 1 / odds.get("away", 1) if odds.get("away") else 0
    }
    
    edges = {
        "home": prediction.get("home_win_prob", 0) - implied_probs["home"],
        "draw": prediction.get("draw_prob", 0) - implied_probs["draw"],
        "away": prediction.get("away_win_prob", 0) - implied_probs["away"]
    }
    
    return f"""Assess value betting opportunities for:

Match: {match.get('home_team')} vs {match.get('away_team')}

Model Predictions vs Implied Probabilities:
| Outcome | Model | Bookmaker | Edge |
|---------|-------|-----------|------|
| Home    | {prediction.get('home_win_prob', 0):.1%} | {implied_probs['home']:.1%} | {edges['home']:+.1%} |
| Draw    | {prediction.get('draw_prob', 0):.1%} | {implied_probs['draw']:.1%} | {edges['draw']:+.1%} |
| Away    | {prediction.get('away_win_prob', 0):.1%} | {implied_probs['away']:.1%} | {edges['away']:+.1%} |

Odds:
- Home: {odds.get('home', 'N/A')}
- Draw: {odds.get('draw', 'N/A')}
- Away: {odds.get('away', 'N/A')}

Analyze:
1. Do any selections show genuine value (edge > 3%)?
2. What factors could the model be underweighting?
3. What factors could the bookmakers be underweighting?
4. Your confidence in each potential value bet
5. Recommended stake (as % of bankroll) using Kelly Criterion
6. Key risks to monitor
"""


def get_sentiment_prompt(articles: str, team: str) -> str:
    """Generate sentiment analysis prompt"""
    
    return f"""Analyze the sentiment of these news articles about {team}:

{articles}

Provide:
1. Overall sentiment score: -1 (very negative) to +1 (very positive)
2. Key positive developments
3. Key negative developments
4. Confidence in sentiment assessment
5. Potential performance impact: High/Medium/Low

Format response as JSON:
{{
    "sentiment_score": 0.0,
    "positive_factors": [],
    "negative_factors": [],
    "confidence": 0.0,
    "performance_impact": "Medium",
    "summary": ""
}}
"""
