"""
Backtest Orchestrator — Ties all 5 layers together.
====================================================
Pipeline: Data Layer → Replay Engine → Strategy → Simulation → Analytics

Each layer is injected, making the orchestrator testable and flexible.
"""

import logging
from typing import List, Optional

from backtester.data_layer.stream_parser import parse_stream_file
from backtester.replay_engine.replay import MarketReplayEngine
from backtester.strategy.base import BaseStrategy
from backtester.strategy.rule_based import RuleBasedStrategy
from backtester.simulation.engine import SimulationEngine
from backtester.simulation.models import SimulationResult
from backtester.analytics.engine import AnalyticsEngine
from backtester.analytics.models import BacktestReport

logger = logging.getLogger("backtest.orchestrator")


class BacktestOrchestrator:
    """Orchestrates the full backtest pipeline.

    Pipeline: Data Layer → Replay Engine → Strategy → Simulation → Analytics

    Each layer is injected, making the orchestrator testable and flexible.
    """

    def __init__(
        self,
        strategy: Optional[BaseStrategy] = None,
        commission_rate: float = 0.0,
    ):
        """Initialize orchestrator with strategy and simulation parameters.

        Args:
            strategy: The betting strategy to use. Defaults to CHIMERA default.
            commission_rate: Betfair commission rate (0.0 = no commission).
        """
        self.strategy = strategy or RuleBasedStrategy.default()
        self.replay_engine = MarketReplayEngine()
        self.simulation_engine = SimulationEngine(commission_rate=commission_rate)
        self.analytics_engine = AnalyticsEngine()

    def run(
        self,
        market_files: List[tuple],  # [(filename, content_str), ...]
        minutes_before_race: int,
    ) -> BacktestReport:
        """Run complete backtest across multiple market files.

        This replaces the original run_backtest() function.
        The signature accepts the same input format for API compatibility.

        Args:
            market_files: List of (filename, file_content_string) tuples
            minutes_before_race: Time offset before race to evaluate strategy

        Returns:
            BacktestReport with same data shape as original BacktestSummary
        """
        simulation_results = []
        total_markets_parsed = 0

        for filename, content in market_files:
            result = self._process_single_market(
                filename, content, minutes_before_race
            )

            if result is not None:
                total_markets_parsed += 1
                simulation_results.append(result)

        # Aggregate all results
        report = self.analytics_engine.compile_report(
            simulation_results, total_markets_parsed
        )

        logger.info(
            f"Backtest complete: {report.total_markets} markets, "
            f"{report.total_bets} bets, "
            f"P&L: £{report.net_profit_loss:.2f}"
        )

        return report

    def _process_single_market(
        self,
        filename: str,
        content: str,
        minutes_before_race: int,
    ) -> Optional[SimulationResult]:
        """Process a single market file through the full pipeline.

        Returns None if parsing fails.
        Returns SimulationResult (possibly with skipped=True if strategy skips).
        """
        # Layer 1: DATA LAYER — Parse NDJSON
        market_data = parse_stream_file(content)
        if not market_data:
            logger.debug(f"Failed to parse: {filename}")
            return None

        # Layer 2: REPLAY ENGINE — Get enriched snapshot at target time
        snapshot = self.replay_engine.get_snapshot_at_offset(
            market_data, minutes_before_race
        )
        if snapshot is None:
            return SimulationResult(
                market_id=market_data.market_id,
                market_name=market_data.market_name,
                venue=market_data.venue,
                skipped=True,
                skip_reason="No snapshot at target time offset",
            )

        # Attach settlement data to snapshot for simulation
        snapshot.settlement = market_data.settlement

        # Layer 3: STRATEGY — Evaluate rules
        strategy_result = self.strategy.evaluate(snapshot)

        if strategy_result.skipped or not strategy_result.instructions:
            return SimulationResult(
                market_id=market_data.market_id,
                market_name=market_data.market_name,
                venue=market_data.venue,
                skipped=True,
                skip_reason=strategy_result.skip_reason or "No bets generated",
            )

        # Layer 4: SIMULATION — Calculate P&L
        sim_result = self.simulation_engine.simulate(
            snapshot, strategy_result.instructions
        )

        return sim_result
