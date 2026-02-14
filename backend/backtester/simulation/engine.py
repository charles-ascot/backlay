"""
Simulation Engine — Calculates P&L from bet instructions and settlement.
========================================================================
Simulates realistic Betfair lay/back bet logic.

P&L rules (preserved exactly from original implementation):
  LAY bet, runner WINNER:  loss = -liability = -(stake * (odds - 1))
  LAY bet, runner LOSER:   profit = +stake
  LAY bet, runner REMOVED: 0
  LAY bet, runner UNKNOWN: 0

  BACK bet, runner WINNER:  profit = +stake * (odds - 1)
  BACK bet, runner LOSER:   loss = -stake
  BACK bet, runner REMOVED: 0
  BACK bet, runner UNKNOWN: 0

Optional commission on net winning bets.
"""

import logging
from typing import List, Tuple

from backtester.strategy.models import BetInstruction
from backtester.simulation.models import BetResult, SimulationResult
from backtester.replay_engine.models import EnrichedSnapshot

logger = logging.getLogger("backtest.simulation")


class SimulationEngine:
    """Simulates bet execution and calculates P&L."""

    def __init__(self, commission_rate: float = 0.0):
        """Initialize with optional commission rate.

        Args:
            commission_rate: Betfair commission as decimal (e.g., 0.05 for 5%)
        """
        self.commission_rate = commission_rate

    def simulate(
        self,
        snapshot: EnrichedSnapshot,
        instructions: List[BetInstruction],
    ) -> SimulationResult:
        """Simulate execution of bet instructions and calculate P&L.

        Args:
            snapshot: The enriched snapshot (contains settlement data and market metadata)
            instructions: List of BetInstructions from strategy evaluation

        Returns:
            SimulationResult with individual BetResults
        """
        bet_results = []

        for instruction in instructions:
            # Look up actual result from settlement
            actual_result = 'UNKNOWN'
            if snapshot.settlement:
                actual_result = snapshot.settlement.get(
                    instruction.selection_id, 'UNKNOWN'
                )

            # Calculate P&L
            profit_loss, commission_paid = self._calculate_pnl(
                instruction, actual_result
            )

            bet_result = BetResult(
                market_id=snapshot.market_id,
                market_name=snapshot.market_name,
                venue=snapshot.venue,
                race_time=snapshot.market_time,
                runner_name=instruction.runner_name,
                selection_id=instruction.selection_id,
                bet_type=instruction.bet_type,
                odds=instruction.price,
                stake=instruction.stake,
                liability=instruction.liability,
                rule_applied=instruction.rule_id,
                actual_result=actual_result,
                profit_loss=round(profit_loss, 2),
                commission_paid=round(commission_paid, 2),
            )
            bet_results.append(bet_result)

        return SimulationResult(
            market_id=snapshot.market_id,
            market_name=snapshot.market_name,
            venue=snapshot.venue,
            bet_results=bet_results,
        )

    def _calculate_pnl(
        self,
        instruction: BetInstruction,
        actual_result: str,
    ) -> Tuple[float, float]:
        """Calculate P&L for a single bet.

        Returns (profit_loss, commission_paid)

        P&L logic preserved exactly from backtest_engine.py.
        Commission applied only to gross profit on winning bets.
        """
        profit_loss = 0.0
        commission_paid = 0.0

        if instruction.bet_type == 'LAY':
            if actual_result == 'WINNER':
                # We laid the winner — we LOSE our liability
                profit_loss = -instruction.liability
            elif actual_result == 'LOSER':
                # We laid a loser — we WIN the stake
                gross_profit = instruction.stake
                commission_paid = round(gross_profit * self.commission_rate, 2)
                profit_loss = gross_profit - commission_paid
            elif actual_result == 'REMOVED':
                # Void — no P&L
                profit_loss = 0.0
            else:
                # UNKNOWN — no settlement data
                profit_loss = 0.0

        elif instruction.bet_type == 'BACK':
            if actual_result == 'WINNER':
                # We backed the winner — we WIN
                gross_profit = instruction.stake * (instruction.price - 1)
                commission_paid = round(gross_profit * self.commission_rate, 2)
                profit_loss = gross_profit - commission_paid
            elif actual_result == 'LOSER':
                # We backed a loser — we LOSE our stake
                profit_loss = -instruction.stake
            elif actual_result == 'REMOVED':
                profit_loss = 0.0
            else:
                profit_loss = 0.0

        return profit_loss, commission_paid
