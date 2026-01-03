"""
Claude (Anthropic) Integration - Reasoning and analysis
"""

import time
from typing import Any, Dict, Optional
from datetime import datetime
import anthropic
import structlog

from .base import BaseLLM, LLMResponse, MatchAnalysis
from .prompts import get_match_analysis_prompt, get_system_prompt

logger = structlog.get_logger()


class ClaudeLLM(BaseLLM):
    """
    Anthropic Claude integration for football analysis.
    
    Best for: Deep reasoning, tactical analysis, long-form insights
    """
    
    MODELS = {
        "claude-3-opus": "claude-3-opus-20240229",
        "claude-3-sonnet": "claude-3-sonnet-20240229",
        "claude-3-haiku": "claude-3-haiku-20240307",
        "claude-3.5-sonnet": "claude-3-5-sonnet-20241022"
    }
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3.5-sonnet",
        max_tokens: int = 1500,
        temperature: float = 0.3
    ):
        model_id = self.MODELS.get(model, model)
        super().__init__(api_key, model_id, max_tokens, temperature)
        
        self.client = anthropic.Anthropic(api_key=api_key)
    
    @property
    def provider_name(self) -> str:
        return "claude"
    
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion using Claude"""
        start_time = time.time()
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                system=kwargs.get("system", get_system_prompt()),
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            latency = (time.time() - start_time) * 1000
            content = response.content[0].text
            tokens = response.usage.input_tokens + response.usage.output_tokens
            
            self._request_count += 1
            self._total_tokens += tokens
            
            logger.debug(
                "claude_completion",
                tokens=tokens,
                latency_ms=latency
            )
            
            return LLMResponse(
                content=content,
                model=self.model,
                provider=self.provider_name,
                tokens_used=tokens,
                latency_ms=latency,
                timestamp=datetime.now(),
                raw_response={"usage": response.usage.model_dump()}
            )
            
        except Exception as e:
            logger.error("claude_error", error=str(e))
            raise
    
    async def analyze_match(
        self,
        home_team: str,
        away_team: str,
        context: Dict[str, Any]
    ) -> MatchAnalysis:
        """Analyze match using Claude's reasoning capabilities"""
        
        prompt = get_match_analysis_prompt(home_team, away_team, context)
        
        response = await self.complete(
            prompt,
            system=get_system_prompt("tactical_analyst")
        )
        
        analysis = self._parse_analysis(response.content, home_team, away_team)
        analysis.model = f"claude:{self.model}"
        
        return analysis
    
    async def get_tactical_breakdown(
        self,
        home_team: str,
        away_team: str,
        context: Dict[str, Any]
    ) -> str:
        """Get detailed tactical breakdown"""
        
        prompt = f"""Provide a detailed tactical breakdown for the match:
{home_team} vs {away_team}

Context:
- Home Team Form: {context.get('home_form', 'N/A')}
- Away Team Form: {context.get('away_form', 'N/A')}
- Home Attack Strength: {context.get('home_attack', 'N/A')}
- Away Defense Strength: {context.get('away_defense', 'N/A')}

Analyze:
1. Expected formations and tactical setups
2. Key battles (midfield, wings, etc.)
3. Potential game-changers
4. Set-piece threats
5. Possible tactical adjustments during the match
"""
        
        response = await self.complete(prompt)
        return response.content
    
    async def assess_value_bet(
        self,
        match: Dict,
        prediction: Dict,
        odds: Dict
    ) -> Dict:
        """Assess whether a bet offers value"""
        
        prompt = f"""Assess this potential value bet:

Match: {match.get('home_team')} vs {match.get('away_team')}

Model Prediction:
- Home Win: {prediction.get('home_win_prob', 0):.1%}
- Draw: {prediction.get('draw_prob', 0):.1%}
- Away Win: {prediction.get('away_win_prob', 0):.1%}

Available Odds:
- Home: {odds.get('home', 0)}
- Draw: {odds.get('draw', 0)}
- Away: {odds.get('away', 0)}

Analyze:
1. Does any selection offer genuine value?
2. What factors might the model be missing?
3. What's your confidence in the value assessment?
4. Recommended stake (as % of bankroll)?
5. Key risks to consider?

Provide structured analysis with clear recommendation.
"""
        
        response = await self.complete(prompt)
        
        return {
            "match": f"{match.get('home_team')} vs {match.get('away_team')}",
            "analysis": response.content,
            "model": self.model
        }
