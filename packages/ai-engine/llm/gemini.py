"""
Google Gemini Integration - Context and multi-modal analysis
"""

import time
from typing import Any, Dict, List, Optional
from datetime import datetime
import google.generativeai as genai
import structlog

from .base import BaseLLM, LLMResponse, MatchAnalysis
from .prompts import get_match_analysis_prompt, get_system_prompt

logger = structlog.get_logger()


class GeminiLLM(BaseLLM):
    """
    Google Gemini integration for football analysis.
    
    Best for: Long context, historical data analysis, pattern recognition
    """
    
    MODELS = {
        "gemini-pro": "gemini-pro",
        "gemini-1.5-pro": "gemini-1.5-pro",
        "gemini-1.5-flash": "gemini-1.5-flash"
    }
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        max_tokens: int = 1000,
        temperature: float = 0.3
    ):
        model_id = self.MODELS.get(model, model)
        super().__init__(api_key, model_id, max_tokens, temperature)
        
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model_id)
    
    @property
    def provider_name(self) -> str:
        return "gemini"
    
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion using Gemini"""
        start_time = time.time()
        
        try:
            # Add system context to prompt
            system = kwargs.get("system", get_system_prompt())
            full_prompt = f"{system}\n\n{prompt}"
            
            response = self.client.generate_content(
                full_prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=kwargs.get("max_tokens", self.max_tokens),
                    temperature=kwargs.get("temperature", self.temperature)
                )
            )
            
            latency = (time.time() - start_time) * 1000
            content = response.text
            
            # Estimate tokens (Gemini doesn't always provide)
            tokens = len(prompt.split()) + len(content.split())
            
            self._request_count += 1
            self._total_tokens += tokens
            
            logger.debug(
                "gemini_completion",
                tokens=tokens,
                latency_ms=latency
            )
            
            return LLMResponse(
                content=content,
                model=self.model,
                provider=self.provider_name,
                tokens_used=tokens,
                latency_ms=latency,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error("gemini_error", error=str(e))
            raise
    
    async def analyze_match(
        self,
        home_team: str,
        away_team: str,
        context: Dict[str, Any]
    ) -> MatchAnalysis:
        """Analyze match using Gemini"""
        
        prompt = get_match_analysis_prompt(home_team, away_team, context)
        
        response = await self.complete(prompt)
        
        analysis = self._parse_analysis(response.content, home_team, away_team)
        analysis.model = f"gemini:{self.model}"
        
        return analysis
    
    async def analyze_historical_patterns(
        self,
        home_team: str,
        away_team: str,
        historical_matches: List[Dict],
        seasons: int = 5
    ) -> Dict:
        """Analyze historical patterns between teams"""
        
        matches_text = "\n".join([
            f"- {m.get('date', 'N/A')}: {m.get('home_team')} {m.get('home_score')}-{m.get('away_score')} {m.get('away_team')}"
            for m in historical_matches[:20]
        ])
        
        prompt = f"""Analyze historical patterns between {home_team} and {away_team}:

Last {len(historical_matches)} meetings:
{matches_text}

Identify:
1. Head-to-head trends (home advantage, scoring patterns)
2. Seasonal patterns (better at certain times of year?)
3. High-scoring vs low-scoring tendency
4. Recent momentum shifts
5. Key patterns that might influence the next meeting
6. Statistical anomalies

Provide structured analysis with data-backed insights.
"""
        
        response = await self.complete(prompt)
        
        return {
            "home_team": home_team,
            "away_team": away_team,
            "matches_analyzed": len(historical_matches),
            "analysis": response.content,
            "model": self.model
        }
    
    async def analyze_league_context(
        self,
        home_team: str,
        away_team: str,
        standings: Dict,
        remaining_fixtures: List[Dict]
    ) -> Dict:
        """Analyze match in context of league situation"""
        
        home_pos = standings.get(home_team, {}).get("position", "N/A")
        away_pos = standings.get(away_team, {}).get("position", "N/A")
        home_pts = standings.get(home_team, {}).get("points", "N/A")
        away_pts = standings.get(away_team, {}).get("points", "N/A")
        
        prompt = f"""Analyze this match in the context of the league situation:

Match: {home_team} (Position: {home_pos}, Points: {home_pts}) vs {away_team} (Position: {away_pos}, Points: {away_pts})

Consider:
1. What does each team need from this match?
2. Title race / European qualification / Relegation implications
3. Motivation levels based on season objectives
4. Fixture congestion (upcoming matches)
5. Historical performance in high-stakes matches
6. Expected approach (attacking vs conservative)

Provide context-rich analysis.
"""
        
        response = await self.complete(prompt)
        
        return {
            "home_team": home_team,
            "away_team": away_team,
            "home_position": home_pos,
            "away_position": away_pos,
            "analysis": response.content,
            "model": self.model
        }
    
    async def find_similar_matches(
        self,
        current_match: Dict,
        historical_data: List[Dict],
        top_n: int = 5
    ) -> List[Dict]:
        """Find historically similar matches for comparison"""
        
        # Create context summary
        context_summary = f"""
Home team attacking strength: {current_match.get('home_attack', 'N/A')}
Away team defensive strength: {current_match.get('away_defense', 'N/A')}
Home form: {current_match.get('home_form', 'N/A')}
Position difference: {current_match.get('position_diff', 'N/A')}
"""
        
        # Sample of historical matches for context
        sample_matches = "\n".join([
            f"{i+1}. {m.get('home_team')} {m.get('home_score', '?')}-{m.get('away_score', '?')} {m.get('away_team')} | Home attack: {m.get('home_attack', 'N/A')}, Form: {m.get('home_form', 'N/A')}"
            for i, m in enumerate(historical_data[:50])
        ])
        
        prompt = f"""Find the most similar historical matches to this upcoming fixture:

Current match context:
{context_summary}

Historical matches:
{sample_matches}

Identify the {top_n} most similar matches based on:
- Team strength profiles
- Form entering the match
- League position context
- Playing style matchup

For each similar match, explain why it's a good comparison and what the outcome was.
"""
        
        response = await self.complete(prompt)
        
        return {
            "current_match": current_match,
            "analysis": response.content,
            "similar_matches_count": top_n,
            "model": self.model
        }
