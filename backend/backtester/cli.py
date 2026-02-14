"""
CLI interface for running backtests from the command line.
==========================================================
Usage:
    python -m backtester data/*.ndjson -m 30
    python -m backtester data/*.ndjson -m 30 -s my_strategy.json -c 0.05
    python -m backtester data/*.ndjson -m 30 --json
"""

import argparse
import json
import sys
import os
import glob
import logging

from backtester.orchestrator import BacktestOrchestrator
from backtester.strategy.rule_based import RuleBasedStrategy


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CHIMERA Backtest Simulator CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m backtester data/*.ndjson -m 30
  python -m backtester data/*.ndjson -m 30 -s custom_strategy.json
  python -m backtester data/*.ndjson -m 30 -c 0.05 --json
        """,
    )

    parser.add_argument(
        "files",
        nargs="+",
        help="NDJSON stream files or glob patterns",
    )
    parser.add_argument(
        "-m", "--minutes-before",
        type=int,
        default=30,
        help="Minutes before race to evaluate strategy (default: 30)",
    )
    parser.add_argument(
        "-s", "--strategy",
        type=str,
        default=None,
        help="Path to strategy JSON file (default: built-in CHIMERA default)",
    )
    parser.add_argument(
        "-c", "--commission",
        type=float,
        default=0.0,
        help="Commission rate as decimal, e.g., 0.05 for 5%% (default: 0.0)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON instead of formatted table",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output JSON report to file path",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Resolve file paths
    file_paths = _resolve_file_paths(args.files)
    if not file_paths:
        print("Error: No files found matching the provided patterns.", file=sys.stderr)
        sys.exit(1)

    # Load strategy
    if args.strategy:
        strategy = RuleBasedStrategy.from_json_file(args.strategy)
    else:
        strategy = RuleBasedStrategy.default()

    # Read files
    market_files = []
    for path in file_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            market_files.append((os.path.basename(path), content))
        except Exception as e:
            print(f"Warning: Failed to read {path}: {e}", file=sys.stderr)
            continue

    if not market_files:
        print("Error: Failed to read any files.", file=sys.stderr)
        sys.exit(1)

    # Run backtest
    orchestrator = BacktestOrchestrator(
        strategy=strategy,
        commission_rate=args.commission,
    )
    report = orchestrator.run(market_files, args.minutes_before)

    # Output results
    if args.json_output or args.output:
        report_dict = _report_to_dict(report, args.minutes_before, strategy)

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report_dict, f, indent=2)
            print(f"Report written to {args.output}")
        else:
            print(json.dumps(report_dict, indent=2))
    else:
        _print_report(report, args.minutes_before, strategy)


def _resolve_file_paths(patterns: list) -> list:
    """Expand glob patterns into actual file paths."""
    paths = []
    for pattern in patterns:
        expanded = glob.glob(pattern)
        if expanded:
            paths.extend(expanded)
        elif os.path.isfile(pattern):
            paths.append(pattern)
    return sorted(set(paths))


def _report_to_dict(report, minutes_before: int, strategy) -> dict:
    """Convert report to JSON-serializable dict."""
    bet_results = []
    for bet in report.bet_results:
        bet_results.append({
            "market_name": bet.market_name,
            "venue": bet.venue,
            "race_time": bet.race_time,
            "runner_name": bet.runner_name,
            "bet_type": bet.bet_type,
            "odds": round(bet.odds, 2),
            "stake": round(bet.stake, 2),
            "liability": round(bet.liability, 2),
            "rule_applied": bet.rule_applied,
            "actual_result": bet.actual_result,
            "profit_loss": round(bet.profit_loss, 2),
        })

    rules_breakdown = []
    for rule, stats in report.results_by_rule.items():
        win_rate = (stats['wins'] / stats['total_bets'] * 100) if stats['total_bets'] > 0 else 0
        rules_breakdown.append({
            "rule": rule,
            "total_bets": stats['total_bets'],
            "wins": stats['wins'],
            "losses": stats['losses'],
            "win_rate": round(win_rate, 1),
            "total_staked": round(stats['total_staked'], 2),
            "total_liability": round(stats['total_liability'], 2),
            "net_pnl": round(stats['net_pnl'], 2),
        })

    return {
        "strategy": {
            "id": strategy.strategy_id,
            "name": strategy.strategy_name,
            "version": strategy.version,
        },
        "minutes_before_race": minutes_before,
        "summary": {
            "total_markets": report.total_markets,
            "markets_with_bets": report.markets_with_bets,
            "markets_skipped": report.markets_skipped,
            "total_bets": report.total_bets,
            "winning_bets": report.winning_bets,
            "losing_bets": report.losing_bets,
            "win_rate": report.win_rate,
            "total_staked": report.total_staked,
            "total_liability": report.total_liability,
            "net_profit_loss": report.net_profit_loss,
        },
        "bet_results": bet_results,
        "rules_breakdown": rules_breakdown,
    }


def _print_report(report, minutes_before: int, strategy):
    """Print formatted report to stdout."""
    print()
    print("=" * 60)
    print("  CHIMERA Backtest Report")
    print("=" * 60)
    print(f"  Strategy:    {strategy.strategy_name}")
    print(f"  Version:     {strategy.version}")
    print(f"  Time offset: {minutes_before} minutes before race")
    print()

    # Summary
    print("  Summary")
    print("  " + "-" * 40)
    print(f"  Markets processed:    {report.total_markets:>6}")
    print(f"  Markets with bets:    {report.markets_with_bets:>6}")
    print(f"  Markets skipped:      {report.markets_skipped:>6}")
    print(f"  Total bets:           {report.total_bets:>6}")
    print(f"  Winning bets:         {report.winning_bets:>6}")
    print(f"  Losing bets:          {report.losing_bets:>6}")
    print(f"  Win rate:           {report.win_rate:>5.1f}%")
    print(f"  Total staked:       £{report.total_staked:>8.2f}")
    print(f"  Total liability:    £{report.total_liability:>8.2f}")

    pnl_sign = "+" if report.net_profit_loss >= 0 else ""
    print(f"  Net P&L:          {pnl_sign}£{report.net_profit_loss:>8.2f}")
    print()

    # Rules breakdown
    if report.results_by_rule:
        print("  Rules Breakdown")
        print("  " + "-" * 40)
        header = f"  {'Rule':<12} {'Bets':>5} {'Wins':>5} {'Loss':>5} {'Win%':>6} {'Staked':>9} {'Liability':>10} {'Net P&L':>10}"
        print(header)
        print("  " + "-" * len(header.strip()))

        for rule, stats in report.results_by_rule.items():
            win_rate = (stats['wins'] / stats['total_bets'] * 100) if stats['total_bets'] > 0 else 0
            pnl_sign = "+" if stats['net_pnl'] >= 0 else ""
            print(
                f"  {rule:<12} {stats['total_bets']:>5} "
                f"{stats['wins']:>5} {stats['losses']:>5} "
                f"{win_rate:>5.1f}% "
                f"£{stats['total_staked']:>7.2f} "
                f"£{stats['total_liability']:>8.2f} "
                f"{pnl_sign}£{stats['net_pnl']:>8.2f}"
            )

    print()
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
