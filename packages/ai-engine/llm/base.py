"""
LLM Base Class - Tüm LLM entegrasyonları için temel sınıf
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import structlog

logger = structlog.get_logger()


@dataclass
class LLMResponse:
    """Container for LLM response"""
    content: str
    model: str
    provider: str
    tokens_used: int
    latency_ms: float
    timestamp: datetime
    raw_response: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class MatchAnalysis:
    """Structured match analysis from LLM"""
    home_team: str
    away_team: str
    prediction: str  # H, D, A
    confidence: float  # 0-1
    reasoning: str
    key_factors: List[str]
    risk_factors: List[str]
    score_prediction: Optional[str] = None
    value_assessment: Optional[str] = None
    model: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "home_team": self.home_team,
            "away_team": self.away_team,
            "prediction": self.prediction,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "key_factors": self.key_factors,
            "risk_factors": self.risk_factors,
            "score_prediction": self.score_prediction,
            "value_assessment": self.value_assessment,
            "model": self.model
        }


class BaseLLM(ABC):
    """
    Abstract base class for LLM providers.
    """
    
    def __init__(
        self, 
        api_key: str,
        model: str,
        max_tokens: int = 1000,
        temperature: float = 0.3
    ):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._request_count = 0
        self._total_tokens = 0
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name (claude, openai, gemini)"""
        pass
    
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Generate completion for prompt.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse with generated content
        """
        pass
    
    @abstractmethod
    async def analyze_match(
        self,
        home_team: str,
        away_team: str,
        context: Dict[str, Any]
    ) -> MatchAnalysis:
        """
        Analyze a football match.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            context: Additional context (stats, form, odds, etc.)
            
        Returns:
            Structured MatchAnalysis
        """
        pass
    
    def get_stats(self) -> Dict:
        """Get usage statistics"""
        return {
            "provider": self.provider_name,
            "model": self.model,
            "requests": self._request_count,
            "total_tokens": self._total_tokens
        }
    
    def _parse_analysis(self, content: str, home_team: str, away_team: str) -> MatchAnalysis:
        """Parse LLM response into structured analysis"""
        # Default parsing - can be overridden by subclasses
        import re
        
        # Extract prediction
        prediction = "D"  # Default
        if re.search(r'\b(home win|home victory|' + re.escape(home_team.lower()) + r' win)', content.lower()):
            prediction = "H"
        elif re.search(r'\b(away win|away victory|' + re.escape(away_team.lower()) + r' win)', content.lower()):
            prediction = "A"
        elif re.search(r'\b(draw|tied|stalemate)', content.lower()):
            prediction = "D"
        
        # Extract confidence
        confidence = 0.5
        conf_match = re.search(r'confidence[:\s]+(\d+(?:\.\d+)?)\s*%?', content.lower())
        if conf_match:
            conf_val = float(conf_match.group(1))
            confidence = conf_val / 100 if conf_val > 1 else conf_val
        
        # Extract score prediction
        score_prediction = None
        score_match = re.search(r'(\d+)\s*[-:]\s*(\d+)', content)
        if score_match:
            score_prediction = f"{score_match.group(1)}-{score_match.group(2)}"
        
        # Extract key factors
        key_factors = []
        factors_section = re.search(r'key factors?:?\s*\n((?:[-•*]\s*.+\n?)+)', content, re.IGNORECASE)
        if factors_section:
            key_factors = [
                f.strip().lstrip('-•* ')
                for f in factors_section.group(1).strip().split('\n')
                if f.strip()
            ]
        
        # Extract risks
        risk_factors = []
        risks_section = re.search(r'risk(?:s| factors?)?:?\s*\n((?:[-•*]\s*.+\n?)+)', content, re.IGNORECASE)
        if risks_section:
            risk_factors = [
                r.strip().lstrip('-•* ')
                for r in risks_section.group(1).strip().split('\n')
                if r.strip()
            ]
        
        return MatchAnalysis(
            home_team=home_team,
            away_team=away_team,
            prediction=prediction,
            confidence=confidence,
            reasoning=content[:500] if len(content) > 500 else content,
            key_factors=key_factors[:5],
            risk_factors=risk_factors[:5],
            score_prediction=score_prediction,
            model=self.model
        )


class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, calls_per_minute: int = 50):
        self.calls_per_minute = calls_per_minute
        self._calls = []
    
    async def acquire(self):
        """Wait if rate limit exceeded"""
        import asyncio
        from datetime import datetime, timedelta
        
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Remove old calls
        self._calls = [t for t in self._calls if t > minute_ago]
        
        if len(self._calls) >= self.calls_per_minute:
            wait_time = (self._calls[0] - minute_ago).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        self._calls.append(now)
