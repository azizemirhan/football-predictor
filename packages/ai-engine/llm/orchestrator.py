"""
LLM Orchestrator - Çoklu LLM koordinasyonu
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
import structlog

from .base import BaseLLM, LLMResponse, MatchAnalysis
from .claude import ClaudeLLM
from .openai_gpt import OpenAILLM
from .gemini import GeminiLLM

logger = structlog.get_logger()


class LLMOrchestrator:
    """
    Orchestrate multiple LLMs for comprehensive analysis.
    
    Strategy:
    - Claude: Deep reasoning and tactical analysis
    - GPT-4: Sentiment analysis and structured outputs  
    - Gemini: Historical patterns and long context
    
    Combines insights from multiple models for robust predictions.
    """
    
    def __init__(
        self,
        claude_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None
    ):
        self.llms: Dict[str, BaseLLM] = {}
        
        if claude_api_key:
            self.llms["claude"] = ClaudeLLM(api_key=claude_api_key)
            logger.info("claude_initialized")
        
        if openai_api_key:
            self.llms["openai"] = OpenAILLM(api_key=openai_api_key)
            logger.info("openai_initialized")
        
        if gemini_api_key:
            self.llms["gemini"] = GeminiLLM(api_key=gemini_api_key)
            logger.info("gemini_initialized")
        
        if not self.llms:
            logger.warning("no_llms_configured")
    
    async def analyze_match_comprehensive(
        self,
        home_team: str,
        away_team: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get comprehensive match analysis from all available LLMs.
        
        Returns combined analysis with:
        - Individual model predictions
        - Consensus prediction
        - Confidence assessment
        - Key insights from each model
        """
        if not self.llms:
            return {"error": "No LLMs configured"}
        
        # Run all analyses in parallel
        tasks = []
        llm_names = []
        
        for name, llm in self.llms.items():
            tasks.append(llm.analyze_match(home_team, away_team, context))
            llm_names.append(name)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        analyses = {}
        predictions = []
        
        for name, result in zip(llm_names, results):
            if isinstance(result, Exception):
                logger.error("llm_analysis_error", llm=name, error=str(result))
                analyses[name] = {"error": str(result)}
            else:
                analyses[name] = result.to_dict()
                predictions.append({
                    "llm": name,
                    "prediction": result.prediction,
                    "confidence": result.confidence
                })
        
        # Calculate consensus
        consensus = self._calculate_consensus(predictions)
        
        return {
            "home_team": home_team,
            "away_team": away_team,
            "individual_analyses": analyses,
            "predictions": predictions,
            "consensus": consensus,
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_consensus(self, predictions: List[Dict]) -> Dict:
        """Calculate consensus prediction from multiple LLMs"""
        if not predictions:
            return {"prediction": None, "confidence": 0, "agreement": 0}
        
        # Count predictions
        counts = {"H": 0, "D": 0, "A": 0}
        weighted_confidence = {"H": 0, "D": 0, "A": 0}
        
        for pred in predictions:
            p = pred["prediction"]
            conf = pred["confidence"]
            counts[p] += 1
            weighted_confidence[p] += conf
        
        # Find majority prediction
        consensus_pred = max(counts, key=counts.get)
        agreement = counts[consensus_pred] / len(predictions)
        
        # Average confidence for consensus prediction
        if counts[consensus_pred] > 0:
            avg_confidence = weighted_confidence[consensus_pred] / counts[consensus_pred]
        else:
            avg_confidence = 0
        
        # Adjust confidence based on agreement
        final_confidence = avg_confidence * (0.5 + 0.5 * agreement)
        
        return {
            "prediction": consensus_pred,
            "confidence": round(final_confidence, 3),
            "agreement": round(agreement, 3),
            "vote_distribution": counts
        }
    
    async def get_specialized_analysis(
        self,
        home_team: str,
        away_team: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get specialized analysis from each LLM based on their strengths.
        
        - Claude: Tactical breakdown
        - GPT: Sentiment from news
        - Gemini: Historical patterns
        """
        results = {}
        
        # Claude for tactical analysis
        if "claude" in self.llms:
            try:
                tactical = await self.llms["claude"].get_tactical_breakdown(
                    home_team, away_team, context
                )
                results["tactical_analysis"] = tactical
            except Exception as e:
                results["tactical_analysis"] = {"error": str(e)}
        
        # GPT for sentiment
        if "openai" in self.llms and context.get("news_articles"):
            try:
                home_sentiment = await self.llms["openai"].analyze_sentiment(
                    context["news_articles"].get(home_team, []),
                    home_team
                )
                away_sentiment = await self.llms["openai"].analyze_sentiment(
                    context["news_articles"].get(away_team, []),
                    away_team
                )
                results["sentiment_analysis"] = {
                    home_team: home_sentiment,
                    away_team: away_sentiment
                }
            except Exception as e:
                results["sentiment_analysis"] = {"error": str(e)}
        
        # Gemini for historical patterns
        if "gemini" in self.llms and context.get("historical_matches"):
            try:
                patterns = await self.llms["gemini"].analyze_historical_patterns(
                    home_team, away_team, context["historical_matches"]
                )
                results["historical_patterns"] = patterns
            except Exception as e:
                results["historical_patterns"] = {"error": str(e)}
        
        return results
    
    async def assess_value_bet(
        self,
        match: Dict,
        prediction: Dict,
        odds: Dict
    ) -> Dict:
        """Get value bet assessment from multiple LLMs"""
        if not self.llms:
            return {"error": "No LLMs configured"}
        
        # Prefer Claude for value assessment
        if "claude" in self.llms:
            return await self.llms["claude"].assess_value_bet(match, prediction, odds)
        
        # Fallback to any available LLM
        llm = next(iter(self.llms.values()))
        
        prompt = f"""Assess value bet for {match.get('home_team')} vs {match.get('away_team')}

Model: H={prediction.get('home_win_prob'):.1%}, D={prediction.get('draw_prob'):.1%}, A={prediction.get('away_win_prob'):.1%}
Odds: H={odds.get('home')}, D={odds.get('draw')}, A={odds.get('away')}

Is there value? Explain briefly and recommend stake if so."""
        
        response = await llm.complete(prompt)
        
        return {
            "match": f"{match.get('home_team')} vs {match.get('away_team')}",
            "analysis": response.content,
            "model": llm.model
        }
    
    def get_stats(self) -> Dict:
        """Get usage statistics for all LLMs"""
        return {
            name: llm.get_stats()
            for name, llm in self.llms.items()
        }


def create_orchestrator(
    claude_key: Optional[str] = None,
    openai_key: Optional[str] = None,
    gemini_key: Optional[str] = None
) -> LLMOrchestrator:
    """Factory function to create orchestrator"""
    import os
    
    return LLMOrchestrator(
        claude_api_key=claude_key or os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=openai_key or os.getenv("OPENAI_API_KEY"),
        gemini_api_key=gemini_key or os.getenv("GOOGLE_API_KEY")
    )
