"""AI-powered strategy stub — future ML/AI-based betting strategy."""

from backtester.strategy.base import BaseStrategy
from backtester.strategy.models import StrategyResult
from backtester.replay_engine.models import EnrichedSnapshot


class AIStrategy(BaseStrategy):
    """Stub for an AI-powered betting strategy.

    Future implementation will use ML models to evaluate markets.
    Currently returns empty results for all markets.
    """

    def __init__(self, model_path: str = ""):
        self.model_path = model_path

    def get_market_filters(self) -> dict:
        """AI strategy has no static market filters."""
        return {}

    def evaluate(self, snapshot: EnrichedSnapshot) -> StrategyResult:
        """Stub: always returns skip result.

        Future: load ML model, extract features from snapshot, predict.
        """
        return StrategyResult(
            skipped=True,
            skip_reason="AI strategy not yet implemented",
        )
