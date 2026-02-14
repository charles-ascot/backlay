"""Analytics models — aggregated reports."""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class RuleStats:
    """Aggregated statistics for a single rule."""
    rule: str
    total_bets: int = 0
    wins: int = 0
    losses: int = 0
    total_staked: float = 0.0
    total_liability: float = 0.0
    net_pnl: float = 0.0

    @property
    def win_rate(self) -> float:
        return round((self.wins / self.total_bets * 100), 1) if self.total_bets > 0 else 0.0


@dataclass
class BacktestReport:
    """Final aggregated report across all markets.

    Field names match the current BacktestSummary exactly
    to preserve the API contract.
    """
    total_markets: int = 0
    markets_with_bets: int = 0
    markets_skipped: int = 0
    total_bets: int = 0
    winning_bets: int = 0
    losing_bets: int = 0
    total_staked: float = 0.0
    total_liability: float = 0.0
    net_profit_loss: float = 0.0
    win_rate: float = 0.0
    results_by_rule: Dict[str, Dict] = field(default_factory=dict)
    bet_results: List = field(default_factory=list)  # List[BetResult]
