"""Base strategy interface — all strategies must implement this."""

from abc import ABC, abstractmethod

from backtester.replay_engine.models import EnrichedSnapshot
from backtester.strategy.models import StrategyResult


class BaseStrategy(ABC):
    """Abstract base class for all betting strategies.

    Contract:
    - evaluate() receives an EnrichedSnapshot with all computed fields
    - Returns a StrategyResult with zero or more BetInstructions
    - Must be stateless (no side effects between calls)
    - Must be deterministic (same input = same output)
    """

    @abstractmethod
    def evaluate(self, snapshot: EnrichedSnapshot) -> StrategyResult:
        """Evaluate the strategy against a market snapshot.

        Args:
            snapshot: Enriched market snapshot with computed fields

        Returns:
            StrategyResult with bet instructions (may be empty if no rules match)
        """
        ...

    @abstractmethod
    def get_market_filters(self) -> dict:
        """Return the market filters this strategy applies to.

        Returns dict with optional keys: country_codes, market_types, event_type_ids
        Each value is a list of strings.
        """
        ...

    def should_evaluate(self, snapshot: EnrichedSnapshot) -> bool:
        """Check if this market passes the strategy's market filters.

        Default implementation checks country_code, market_type, event_type_id
        against get_market_filters(). Subclasses can override for custom logic.
        """
        filters = self.get_market_filters()
        if not filters:
            return True

        if filters.get("country_codes") and snapshot.country_code not in filters["country_codes"]:
            return False
        if filters.get("market_types") and snapshot.market_type not in filters["market_types"]:
            return False
        if filters.get("event_type_ids") and snapshot.event_type_id not in filters["event_type_ids"]:
            return False

        return True
