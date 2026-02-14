"""Simulation models — bet results after settlement."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class BetResult:
    """Result of a single bet after settlement and P&L calculation.

    Preserves all fields the frontend expects.
    """
    market_id: str
    market_name: str
    venue: str
    race_time: str             # ISO format
    runner_name: str
    selection_id: int
    bet_type: str              # 'LAY' or 'BACK'
    odds: float
    stake: float
    liability: float
    rule_applied: str          # Rule ID e.g. "RULE_1"
    actual_result: str         # 'WINNER' | 'LOSER' | 'REMOVED' | 'UNKNOWN'
    profit_loss: float
    commission_paid: float = 0.0


@dataclass
class SimulationResult:
    """Results from simulating all bets for a single market."""
    market_id: str
    market_name: str
    venue: str
    bet_results: List[BetResult] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""
