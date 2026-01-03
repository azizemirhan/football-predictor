"""
OpenAI GPT Integration - Sentiment and news analysis
"""

import time
from typing import Any, Dict, List, Optional
from datetime import datetime
from openai import AsyncOpenAI
import structlog

from .base import BaseLLM, LLMResponse, MatchAnalysis
from .prompts import get_match_analysis_prompt, get_system_prompt

logger = structlog.get_logger()


class OpenAILLM(BaseLLM):
    """
    OpenAI GPT integration for football analysis.
    
    Best for: Sentiment analysis, news summarization, structured outputs
    """
    
    MODELS = {
        "gpt-4": "gpt-4",
        "gpt-4-turbo": "gpt-4-turbo-preview",
        "gpt-4o": "gpt-4o",
        "gpt-4o-mini": "gpt-4o-mini",
        "gpt-3.5-turbo": "gpt-3.5-turbo"
    }
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        max_tokens: int = 1000,
        temperature: float = 0.3
    ):
        model_id = self.MODELS.get(model, model)
        super().__init__(api_key, model_id, max_tokens, temperature)
        
        self.client = AsyncOpenAI(api_key=api_key)
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion using GPT"""
        start_time = time.time()
        
        try:
            messages = [
                {"role": "system", "content": kwargs.get("system", get_system_prompt())},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature)
            )
            
            latency = (time.time() - start_time) * 1000
            content = response.choices[0].message.content
            tokens = response.usage.total_tokens
            
            self._request_count += 1
            self._total_tokens += tokens
            
            logger.debug(
                "openai_completion",
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
            logger.error("openai_error", error=str(e))
            raise
    
    async def analyze_match(
        self,
        home_team: str,
        away_team: str,
        context: Dict[str, Any]
    ) -> MatchAnalysis:
        """Analyze match using GPT"""
        
        prompt = get_match_analysis_prompt(home_team, away_team, context)
        
        response = await self.complete(prompt)
        
        analysis = self._parse_analysis(response.content, home_team, away_team)
        analysis.model = f"openai:{self.model}"
        
        return analysis
    
    async def analyze_sentiment(
        self,
        news_articles: List[Dict],
        team: str
    ) -> Dict:
        """Analyze sentiment from news articles for a team"""
        
        articles_text = "\n\n".join([
            f"Title: {a.get('title', '')}\nContent: {a.get('content', '')[:500]}"
            for a in news_articles[:5]
        ])
        
        prompt = f"""Analyze the sentiment of these news articles about {team}.

Articles:
{articles_text}

Provide:
1. Overall sentiment score (-1 to 1, where -1 is very negative, 1 is very positive)
2. Key positive factors
3. Key negative factors (injuries, controversies, etc.)
4. Impact on upcoming match performance (high/medium/low)
5. Brief summary

Format as JSON.
"""
        
        response = await self.complete(
            prompt,
            system="You are a football news analyst. Output valid JSON only."
        )
        
        # Try to parse JSON
        try:
            import json
            # Find JSON in response
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content)
        except:
            return {
                "raw_analysis": response.content,
                "team": team,
                "error": "Could not parse JSON"
            }
    
    async def summarize_team_news(
        self,
        news_articles: List[Dict],
        team: str
    ) -> str:
        """Summarize news about a team"""
        
        articles_text = "\n".join([
            f"- {a.get('title', '')}"
            for a in news_articles[:10]
        ])
        
        prompt = f"""Summarize the latest news about {team}:

Headlines:
{articles_text}

Provide a brief summary (2-3 sentences) focusing on:
- Team news and injuries
- Form and morale
- Any controversies or distractions
"""
        
        response = await self.complete(prompt)
        return response.content
    
    async def analyze_injury_impact(
        self,
        team: str,
        injured_players: List[Dict],
        upcoming_opponent: str
    ) -> Dict:
        """Analyze impact of injuries on upcoming match"""
        
        injuries = "\n".join([
            f"- {p.get('name')} ({p.get('position')}): {p.get('injury_type', 'Unknown')}"
            for p in injured_players
        ])
        
        prompt = f"""Analyze the impact of these injuries for {team} against {upcoming_opponent}:

Injured Players:
{injuries}

Analyze:
1. Overall impact on team strength (percentage reduction)
2. Specific areas weakened
3. Possible tactical adjustments
4. Historical performance without these players
5. Rating adjustment recommendation (Elo points)

Output as JSON.
"""
        
        response = await self.complete(
            prompt,
            system="You are a football analyst. Output valid JSON."
        )
        
        try:
            import json
            content = response.content
            if "```" in content:
                content = content.split("```")[1].split("```")[0]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except:
            return {"raw_analysis": response.content}
