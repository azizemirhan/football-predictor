"""
LLM Module - Multi-LLM orchestration for football analysis
"""

from .base import BaseLLM, LLMResponse, MatchAnalysis, RateLimiter
from .claude import ClaudeLLM
from .openai_gpt import OpenAILLM
from .gemini import GeminiLLM
from .orchestrator import LLMOrchestrator, create_orchestrator
from .prompts import (
    get_system_prompt,
    get_match_analysis_prompt,
    get_value_bet_prompt,
    get_sentiment_prompt
)

__all__ = [
    "BaseLLM",
    "LLMResponse",
    "MatchAnalysis",
    "RateLimiter",
    "ClaudeLLM",
    "OpenAILLM",
    "GeminiLLM",
    "LLMOrchestrator",
    "create_orchestrator",
    "get_system_prompt",
    "get_match_analysis_prompt",
    "get_value_bet_prompt",
    "get_sentiment_prompt"
]
