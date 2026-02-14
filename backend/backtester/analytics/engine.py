"""
Analytics Engine — Aggregates simulation results into reports.
==============================================================
Produces the same output shape as the original BacktestSummary
to preserve the API contract.
"""

from typing import List, Dict

from backtester.simulation.models import BetResult, SimulationResult
from backtester.analytics.models import BacktestReport, RuleStats


class AnalyticsEngine:
    """Aggregates bet results into the final report."""

    def compile_report(
        self,
        simulation_results: List[SimulationResult],
        total_markets_parsed: int,
    ) -> BacktestReport:
        """Compile all simulation results into a BacktestReport.

        Logic extracted from original run_backtest() aggregation.

        Args:
            simulation_results: Results from each market simulation
            total_markets_parsed: Total files that parsed successfully

        Returns:
            BacktestReport matching the current API response shape
        """
        # Collect all bet results and count markets
        all_bet_results = []
        markets_with_bets = 0
        markets_skipped = 0

        for sim_result in simulation_results:
            if sim_result.skipped or not sim_result.bet_results:
                markets_skipped += 1
            else:
                markets_with_bets += 1
                all_bet_results.extend(sim_result.bet_results)

        # Calculate aggregated statistics
        total_bets = len(all_bet_results)
        winning_bets = sum(1 for b in all_bet_results if b.profit_loss > 0)
        losing_bets = sum(1 for b in all_bet_results if b.profit_loss < 0)
        total_staked = sum(b.stake for b in all_bet_results)
        total_liability = sum(b.liability for b in all_bet_results)
        net_pnl = sum(b.profit_loss for b in all_bet_results)
        win_rate = (winning_bets / total_bets * 100) if total_bets > 0 else 0.0

        # Compute per-rule breakdown
        results_by_rule = self._compute_rule_breakdown(all_bet_results)

        return BacktestReport(
            total_markets=total_markets_parsed,
            markets_with_bets=markets_with_bets,
            markets_skipped=markets_skipped,
            total_bets=total_bets,
            winning_bets=winning_bets,
            losing_bets=losing_bets,
            total_staked=round(total_staked, 2),
            total_liability=round(total_liability, 2),
            net_profit_loss=round(net_pnl, 2),
            win_rate=round(win_rate, 1),
            results_by_rule=results_by_rule,
            bet_results=all_bet_results,
        )

    def _compute_rule_breakdown(
        self,
        all_bet_results: List[BetResult],
    ) -> Dict[str, Dict]:
        """Compute per-rule statistics.

        Returns dict matching the current results_by_rule format:
        {rule_id: {total_bets, wins, losses, total_staked, total_liability, net_pnl}}

        Logic preserved exactly from backtest_engine.py lines 180-201.
        """
        results_by_rule = {}

        for bet in all_bet_results:
            rule = bet.rule_applied
            if rule not in results_by_rule:
                results_by_rule[rule] = {
                    'total_bets': 0,
                    'wins': 0,
                    'losses': 0,
                    'total_staked': 0.0,
                    'total_liability': 0.0,
                    'net_pnl': 0.0,
                }

            results_by_rule[rule]['total_bets'] += 1
            results_by_rule[rule]['total_staked'] += bet.stake
            results_by_rule[rule]['total_liability'] += bet.liability
            results_by_rule[rule]['net_pnl'] += bet.profit_loss

            if bet.profit_loss > 0:
                results_by_rule[rule]['wins'] += 1
            elif bet.profit_loss < 0:
                results_by_rule[rule]['losses'] += 1

        return results_by_rule
