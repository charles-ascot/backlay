"""
JSON-driven Rule-Based Strategy Engine
=======================================
Evaluates market snapshots against a JSON rule definition.
No hardcoded rule logic — all behavior is driven by the strategy config.

Supports:
- Multiple rules with priority ordering
- Multiple conditions per rule (AND logic)
- Multiple actions per rule
- stop_on_match to prevent lower-priority rule evaluation
- Dynamic operator comparison (lt, lte, gt, gte, eq)
- Targets: favourite, second_favourite
- Bet types: LAY, BACK
"""

import json
import operator
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from backtester.strategy.base import BaseStrategy
from backtester.strategy.models import BetInstruction, StrategyResult
from backtester.replay_engine.models import EnrichedSnapshot

logger = logging.getLogger("backtest.strategy")

# Operator lookup table
OPERATORS = {
    "lt": operator.lt,
    "lte": operator.le,
    "gt": operator.gt,
    "gte": operator.ge,
    "eq": operator.eq,
}


class RuleBasedStrategy(BaseStrategy):
    """Strategy driven by a JSON rule definition."""

    def __init__(self, strategy_config: dict):
        """Initialize with a strategy configuration dict.

        Args:
            strategy_config: Dict matching the CHIMERA strategy JSON schema.
                Must have keys: id, name, version, market_filters, rules
        """
        self.config = strategy_config
        self.strategy_id = strategy_config.get("id", "unknown")
        self.strategy_name = strategy_config.get("name", "Unknown Strategy")
        self.version = strategy_config.get("version", "0.0")

        # Pre-sort rules by priority
        self._rules = sorted(
            strategy_config.get("rules", []),
            key=lambda r: r.get("priority", 999),
        )

    @classmethod
    def from_json_file(cls, path: str) -> 'RuleBasedStrategy':
        """Load strategy from a JSON file path."""
        with open(path, 'r') as f:
            config = json.load(f)
        return cls(config)

    @classmethod
    def default(cls) -> 'RuleBasedStrategy':
        """Load the built-in CHIMERA default strategy."""
        default_path = Path(__file__).parent / "chimera_default.json"
        return cls.from_json_file(str(default_path))

    def get_market_filters(self) -> dict:
        """Return market_filters from the strategy config."""
        return self.config.get("market_filters", {})

    def evaluate(self, snapshot: EnrichedSnapshot) -> StrategyResult:
        """Evaluate all rules against the snapshot.

        Rules are evaluated in priority order (pre-sorted).
        If a rule matches and has stop_on_match=True, no further rules are evaluated.
        """
        result = StrategyResult()

        # Check market filters first
        if not self.should_evaluate(snapshot):
            result.skipped = True
            result.skip_reason = (
                f"Market filtered: {snapshot.country_code}/{snapshot.market_type}"
            )
            return result

        # Must have a favourite to evaluate rules
        if snapshot.fav_lay_odds is None:
            result.skipped = True
            result.skip_reason = "No active runners with available lay prices"
            return result

        # Evaluate rules in priority order
        for rule in self._rules:
            matched_instructions = self._evaluate_rule(rule, snapshot)

            if matched_instructions is not None:
                # Rule matched — add instructions
                result.instructions.extend(matched_instructions)
                result.rule_applied = rule["id"]

                if rule.get("stop_on_match", True):
                    break

        # If no rules matched and no instructions generated
        if not result.instructions and not result.skipped:
            result.skipped = True
            result.skip_reason = "No rules matched"

        return result

    def _evaluate_rule(
        self,
        rule: dict,
        snapshot: EnrichedSnapshot,
    ) -> Optional[List[BetInstruction]]:
        """Evaluate a single rule against a snapshot.

        Returns list of BetInstructions if ALL conditions match, None otherwise.
        """
        conditions = rule.get("conditions", [])

        # All conditions must pass (AND logic)
        for condition in conditions:
            if not self._check_condition(condition, snapshot):
                return None

        # All conditions passed — create instructions from actions
        instructions = self._create_instructions(
            rule.get("actions", []),
            rule["id"],
            snapshot,
        )

        # Only count as matched if at least one instruction was created
        # (a target might not exist, e.g., no second_favourite)
        if not instructions:
            return None

        return instructions

    def _check_condition(
        self,
        condition: dict,
        snapshot: EnrichedSnapshot,
    ) -> bool:
        """Check a single condition against the snapshot.

        condition format: {"field": "fav_lay_odds", "operator": "lt", "value": 2.0}
        """
        field_name = condition.get("field", "")
        op_name = condition.get("operator", "")
        target_value = condition.get("value")

        # Resolve field value from snapshot
        field_value = self._resolve_field(field_name, snapshot)
        if field_value is None:
            return False  # Can't evaluate condition without data

        # Look up operator function
        op_func = OPERATORS.get(op_name)
        if op_func is None:
            logger.warning(f"Unknown operator: {op_name}")
            return False

        return op_func(field_value, target_value)

    def _resolve_field(
        self,
        field_name: str,
        snapshot: EnrichedSnapshot,
    ) -> Optional[float]:
        """Resolve a field name to its numeric value from the snapshot.

        Returns None if the field is not available (e.g., no second favourite).
        """
        field_map = {
            "fav_lay_odds": snapshot.fav_lay_odds,
            "second_lay_odds": snapshot.second_lay_odds,
            "gap_to_second": snapshot.gap_to_second,
        }
        return field_map.get(field_name)

    def _create_instructions(
        self,
        actions: List[dict],
        rule_id: str,
        snapshot: EnrichedSnapshot,
    ) -> List[BetInstruction]:
        """Create BetInstructions from rule actions.

        action format: {"target": "favourite", "bet_type": "LAY", "stake": 3.0}
        """
        instructions = []
        for action in actions:
            target = self._resolve_target(action.get("target", ""), snapshot)
            if target is None:
                continue  # Skip if target runner doesn't exist

            selection_id, runner_name, price = target
            instructions.append(BetInstruction(
                selection_id=selection_id,
                runner_name=runner_name,
                bet_type=action.get("bet_type", "LAY"),
                price=price,
                stake=action.get("stake", 1.0),
                rule_id=rule_id,
            ))

        return instructions

    def _resolve_target(
        self,
        target: str,
        snapshot: EnrichedSnapshot,
    ) -> Optional[Tuple[int, str, float]]:
        """Resolve a target name to (selection_id, runner_name, price).

        Targets: 'favourite', 'second_favourite'
        Returns None if target runner doesn't exist.
        """
        if target == "favourite" and snapshot.favourite:
            if snapshot.favourite.best_lay_price is not None:
                return (
                    snapshot.favourite.selection_id,
                    snapshot.favourite.runner_name,
                    snapshot.favourite.best_lay_price,
                )
        elif target == "second_favourite" and snapshot.second_favourite:
            if snapshot.second_favourite.best_lay_price is not None:
                return (
                    snapshot.second_favourite.selection_id,
                    snapshot.second_favourite.runner_name,
                    snapshot.second_favourite.best_lay_price,
                )
        return None
