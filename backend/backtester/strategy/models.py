"""Strategy models — bet instructions and strategy evaluation results."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class BetInstruction:
    """A single bet instruction produced by a strategy.

    Bet-type agnostic — supports both LAY and BACK.
    """
    selection_id: int
    runner_name: str
    bet_type: str              # 'LAY' or 'BACK'
    price: float               # The odds
    stake: float               # The backer's stake (for LAY) or our stake (for BACK)
    rule_id: str               # Which rule produced this, e.g. "RULE_1"

    @property
    def liability(self) -> float:
        """Calculate liability based on bet type."""
        if self.bet_type == 'LAY':
            return round(self.stake * (self.price - 1), 2)
        else:  # BACK
            return round(self.stake, 2)


@dataclass
class StrategyResult:
    """The output of strategy evaluation for a single market snapshot."""
    instructions: List[BetInstruction] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""
    rule_applied: str = ""     # ID of the matched rule
