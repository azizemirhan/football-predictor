"""
Value Bet Calculator - Değer bahis tespiti ve Kelly Criterion
"""

import numpy as np
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import structlog

logger = structlog.get_logger()


@dataclass
class ValueBet:
    """Value bet data container"""
    match_id: str
    home_team: str
    away_team: str
    selection: str  # home_win, draw, away_win, over_2.5, etc.
    market_type: str
    bookmaker: str
    odds: float
    predicted_prob: float
    implied_prob: float
    edge: float
    kelly_fraction: float
    recommended_stake: float
    confidence: float
    
    def to_dict(self) -> Dict:
        return {
            "match_id": self.match_id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "selection": self.selection,
            "market_type": self.market_type,
            "bookmaker": self.bookmaker,
            "odds": round(self.odds, 2),
            "predicted_prob": round(self.predicted_prob, 4),
            "implied_prob": round(self.implied_prob, 4),
            "edge": round(self.edge, 4),
            "kelly_fraction": round(self.kelly_fraction, 4),
            "recommended_stake": round(self.recommended_stake, 4),
            "confidence": round(self.confidence, 4)
        }


class ValueBetCalculator:
    """
    Calculate value bets using prediction probabilities and betting odds.
    
    Features:
    - Expected Value (EV) calculation
    - Kelly Criterion stake sizing
    - Edge detection
    - Risk management
    """
    
    def __init__(
        self,
        min_edge: float = 0.03,  # Minimum 3% edge
        min_odds: float = 1.30,
        max_odds: float = 10.0,
        kelly_fraction: float = 0.25,  # Fractional Kelly
        max_stake: float = 0.10,  # Max 10% of bankroll
        confidence_threshold: float = 0.5
    ):
        self.min_edge = min_edge
        self.min_odds = min_odds
        self.max_odds = max_odds
        self.kelly_fraction = kelly_fraction
        self.max_stake = max_stake
        self.confidence_threshold = confidence_threshold
    
    def find_value_bets(
        self,
        prediction: Dict,
        odds: Dict,
        match_info: Optional[Dict] = None
    ) -> List[ValueBet]:
        """
        Find value bets for a match.
        
        Args:
            prediction: Model prediction with probabilities
            odds: Available betting odds
            match_info: Additional match information
            
        Returns:
            List of value bets found
        """
        value_bets = []
        
        match_id = prediction.get("match_id") or match_info.get("id", "")
        home_team = prediction.get("home_team", "")
        away_team = prediction.get("away_team", "")
        confidence = prediction.get("confidence", 0.5)
        
        # Skip low confidence predictions
        if confidence < self.confidence_threshold:
            return value_bets
        
        # 1X2 Market
        selections = [
            ("home_win", "1x2", prediction.get("home_win_prob", 0)),
            ("draw", "1x2", prediction.get("draw_prob", 0)),
            ("away_win", "1x2", prediction.get("away_win_prob", 0))
        ]
        
        # Over/Under 2.5 (if expected goals available)
        exp_home = prediction.get("expected_home_goals")
        exp_away = prediction.get("expected_away_goals")
        
        if exp_home is not None and exp_away is not None:
            over_prob = self._calculate_over_probability(exp_home, exp_away, 2.5)
            selections.append(("over_2.5", "totals", over_prob))
            selections.append(("under_2.5", "totals", 1 - over_prob))
        
        # Check each selection
        for selection, market, predicted_prob in selections:
            if predicted_prob <= 0:
                continue
            
            # Get best odds for this selection
            selection_odds = self._get_selection_odds(odds, selection, market)
            
            for bookmaker, bet_odds in selection_odds.items():
                if not self._is_valid_odds(bet_odds):
                    continue
                
                # Calculate value
                implied_prob = 1 / bet_odds
                edge = predicted_prob - implied_prob
                
                if edge >= self.min_edge:
                    # Calculate Kelly stake
                    kelly = self._kelly_criterion(predicted_prob, bet_odds)
                    recommended_stake = self._adjust_stake(kelly, confidence)
                    
                    value_bet = ValueBet(
                        match_id=match_id,
                        home_team=home_team,
                        away_team=away_team,
                        selection=selection,
                        market_type=market,
                        bookmaker=bookmaker,
                        odds=bet_odds,
                        predicted_prob=predicted_prob,
                        implied_prob=implied_prob,
                        edge=edge,
                        kelly_fraction=kelly,
                        recommended_stake=recommended_stake,
                        confidence=confidence
                    )
                    value_bets.append(value_bet)
        
        # Sort by edge (highest first)
        value_bets.sort(key=lambda x: x.edge, reverse=True)
        
        return value_bets
    
    def _get_selection_odds(
        self, 
        odds: Dict, 
        selection: str, 
        market: str
    ) -> Dict[str, float]:
        """Get odds for a specific selection from all bookmakers"""
        result = {}
        
        # Map selection to odds keys
        key_mapping = {
            "home_win": ["home", "Home Team", "1"],
            "draw": ["draw", "Draw", "X"],
            "away_win": ["away", "Away Team", "2"],
            "over_2.5": ["over_2.5", "Over_2.5", "over"],
            "under_2.5": ["under_2.5", "Under_2.5", "under"]
        }
        
        possible_keys = key_mapping.get(selection, [selection])
        
        for bookmaker, markets in odds.items():
            if isinstance(markets, dict):
                for market_name, outcomes in markets.items():
                    if isinstance(outcomes, dict):
                        for key in possible_keys:
                            if key in outcomes:
                                result[bookmaker] = outcomes[key]
                                break
        
        # Also check flat structure
        if "best_odds" in odds:
            best = odds["best_odds"]
            for key in possible_keys:
                if key in best:
                    result["best"] = best[key]
                    break
        
        return result
    
    def _is_valid_odds(self, odds: float) -> bool:
        """Check if odds are within acceptable range"""
        return self.min_odds <= odds <= self.max_odds
    
    def _kelly_criterion(self, prob: float, odds: float) -> float:
        """
        Calculate Kelly Criterion stake.
        
        Kelly = (b*p - q) / b
        where:
        - b = odds - 1 (net odds)
        - p = probability of winning
        - q = probability of losing (1 - p)
        """
        if prob <= 0 or prob >= 1 or odds <= 1:
            return 0
        
        b = odds - 1
        p = prob
        q = 1 - p
        
        kelly = (b * p - q) / b
        
        # Apply fractional Kelly
        return max(0, kelly * self.kelly_fraction)
    
    def _adjust_stake(self, kelly: float, confidence: float) -> float:
        """Adjust stake based on confidence and limits"""
        # Scale by confidence
        adjusted = kelly * confidence
        
        # Apply maximum stake limit
        return min(adjusted, self.max_stake)
    
    def _calculate_over_probability(
        self, 
        exp_home: float, 
        exp_away: float, 
        line: float
    ) -> float:
        """Calculate probability of over N goals using Poisson"""
        from scipy import stats
        
        total_goals = exp_home + exp_away
        
        # P(total > line) = 1 - P(total <= line)
        under_prob = 0
        for goals in range(int(line) + 1):
            # Approximate with Poisson
            under_prob += stats.poisson.pmf(goals, total_goals)
        
        return 1 - under_prob
    
    def calculate_expected_value(self, prob: float, odds: float) -> float:
        """Calculate expected value of a bet"""
        return (prob * odds) - 1
    
    def calculate_roi(self, prob: float, odds: float) -> float:
        """Calculate return on investment"""
        ev = self.calculate_expected_value(prob, odds)
        return ev * 100  # As percentage


class BankrollManager:
    """
    Manage betting bankroll and track performance.
    """
    
    def __init__(
        self,
        initial_bankroll: float = 1000.0,
        max_exposure: float = 0.25,  # Max 25% of bankroll at risk
        stop_loss: float = 0.20,  # Stop at 20% loss
        target_profit: float = 0.50  # Target 50% profit
    ):
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.max_exposure = max_exposure
        self.stop_loss = stop_loss
        self.target_profit = target_profit
        
        self.pending_bets = []
        self.settled_bets = []
        self.daily_pnl = []
    
    def can_place_bet(self, stake: float) -> bool:
        """Check if bet can be placed within limits"""
        # Check bankroll
        if stake > self.current_bankroll:
            return False
        
        # Check exposure
        pending_exposure = sum(b["stake"] for b in self.pending_bets)
        if (pending_exposure + stake) / self.initial_bankroll > self.max_exposure:
            return False
        
        # Check stop loss
        if self.current_bankroll < self.initial_bankroll * (1 - self.stop_loss):
            logger.warning("stop_loss_triggered")
            return False
        
        return True
    
    def place_bet(self, bet: ValueBet, stake: float) -> bool:
        """Place a bet"""
        if not self.can_place_bet(stake):
            return False
        
        self.pending_bets.append({
            "bet": bet.to_dict(),
            "stake": stake,
            "potential_return": stake * bet.odds
        })
        
        self.current_bankroll -= stake
        
        logger.info(
            "bet_placed",
            selection=bet.selection,
            odds=bet.odds,
            stake=stake
        )
        
        return True
    
    def settle_bet(self, bet_id: str, won: bool, actual_return: float = 0):
        """Settle a pending bet"""
        for i, pending in enumerate(self.pending_bets):
            if pending["bet"].get("match_id") == bet_id:
                bet = self.pending_bets.pop(i)
                
                pnl = actual_return - bet["stake"] if won else -bet["stake"]
                self.current_bankroll += actual_return if won else 0
                
                bet["settled"] = True
                bet["won"] = won
                bet["pnl"] = pnl
                
                self.settled_bets.append(bet)
                self.daily_pnl.append(pnl)
                
                logger.info(
                    "bet_settled",
                    won=won,
                    pnl=pnl,
                    bankroll=self.current_bankroll
                )
                
                return True
        
        return False
    
    def get_stats(self) -> Dict:
        """Get bankroll statistics"""
        total_bets = len(self.settled_bets)
        won_bets = sum(1 for b in self.settled_bets if b.get("won"))
        
        total_staked = sum(b["stake"] for b in self.settled_bets)
        total_pnl = sum(b.get("pnl", 0) for b in self.settled_bets)
        
        return {
            "initial_bankroll": self.initial_bankroll,
            "current_bankroll": round(self.current_bankroll, 2),
            "pnl": round(total_pnl, 2),
            "pnl_percent": round(total_pnl / self.initial_bankroll * 100, 2),
            "total_bets": total_bets,
            "won_bets": won_bets,
            "win_rate": round(won_bets / total_bets * 100, 2) if total_bets > 0 else 0,
            "total_staked": round(total_staked, 2),
            "roi": round(total_pnl / total_staked * 100, 2) if total_staked > 0 else 0,
            "pending_bets": len(self.pending_bets),
            "pending_exposure": sum(b["stake"] for b in self.pending_bets)
        }
