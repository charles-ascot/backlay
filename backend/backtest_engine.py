"""
Backtest Engine - Simulate Betting on Historical Data
======================================================
Loads historical stream files, applies rules at chosen time offset,
simulates bet placement, and calculates P&L based on actual settlement.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

from stream_parser import MarketData, MarketSnapshot, find_snapshot_at_offset
from rules import Runner, apply_rules, RuleResult, LayInstruction


@dataclass
class BetResult:
    """Result of a single bet after settlement."""
    market_id: str
    market_name: str
    venue: str
    race_time: str
    runner_name: str
    selection_id: int
    bet_type: str  # 'LAY'
    odds: float
    stake: float
    liability: float
    rule_applied: str
    actual_result: str  # 'WINNER' | 'LOSER' | 'REMOVED'
    profit_loss: float
    

@dataclass
class BacktestSummary:
    """Aggregated results across all markets."""
    total_markets: int
    markets_with_bets: int
    markets_skipped: int
    total_bets: int
    winning_bets: int
    losing_bets: int
    total_staked: float
    total_liability: float
    net_profit_loss: float
    win_rate: float
    results_by_rule: Dict[str, Dict]
    bet_results: List[BetResult]


def simulate_market(
    market_data: MarketData,
    minutes_before_race: int
) -> tuple[Optional[RuleResult], List[BetResult]]:
    """
    Simulate betting on a single market at specified time offset.
    
    Returns:
        (rule_result, bet_results) - the rule evaluation and P&L outcomes
    """
    # Find snapshot at target time
    snapshot = find_snapshot_at_offset(market_data, minutes_before_race)
    if not snapshot:
        return None, []
    
    # Convert snapshot to Runner objects (expected by rules)
    runners = []
    for r in snapshot.runners:
        runner = Runner(
            selection_id=r['selection_id'],
            runner_name=r['runner_name'],
            handicap=0.0,
            best_available_to_lay=r['best_lay_price'],
            status='ACTIVE'
        )
        runners.append(runner)
    
    # Apply rules
    rule_result = apply_rules(
        market_id=market_data.market_id,
        market_name=market_data.market_name,
        venue=market_data.venue,
        race_time=market_data.market_time,
        runners=runners,
    )
    
    # If no bets placed (skipped or no instructions)
    if rule_result.skipped or not rule_result.instructions:
        return rule_result, []
    
    # Calculate P&L for each bet
    bet_results = []
    for instruction in rule_result.instructions:
        actual_result = 'UNKNOWN'
        profit_loss = 0.0
        
        if market_data.settlement:
            runner_status = market_data.settlement.get(instruction.selection_id, 'UNKNOWN')
            actual_result = runner_status
            
            if runner_status == 'WINNER':
                # We laid the winner - we LOSE our liability
                profit_loss = -instruction.liability
            elif runner_status == 'LOSER':
                # We laid a loser - we WIN the stake
                profit_loss = instruction.size
            elif runner_status == 'REMOVED':
                # Void - no P&L
                profit_loss = 0.0
        
        bet_result = BetResult(
            market_id=market_data.market_id,
            market_name=market_data.market_name,
            venue=market_data.venue,
            race_time=market_data.market_time,
            runner_name=instruction.runner_name,
            selection_id=instruction.selection_id,
            bet_type='LAY',
            odds=instruction.price,
            stake=instruction.size,
            liability=instruction.liability,
            rule_applied=instruction.rule_applied,
            actual_result=actual_result,
            profit_loss=profit_loss,
        )
        bet_results.append(bet_result)
    
    return rule_result, bet_results


def run_backtest(
    market_files: List[tuple[str, str]],  # [(filename, content), ...]
    minutes_before_race: int
) -> BacktestSummary:
    """
    Run backtest across multiple market files.
    
    Args:
        market_files: List of (filename, file_content) tuples
        minutes_before_race: Time offset to place bets (e.g., 30 = 30 min before)
    
    Returns:
        BacktestSummary with aggregated results
    """
    from stream_parser import parse_stream_file
    
    all_bet_results = []
    markets_processed = 0
    markets_with_bets = 0
    markets_skipped = 0
    
    for filename, content in market_files:
        # Parse the stream file
        market_data = parse_stream_file(content)
        if not market_data:
            markets_skipped += 1
            continue
        
        markets_processed += 1
        
        # Simulate betting on this market
        rule_result, bet_results = simulate_market(market_data, minutes_before_race)
        
        if bet_results:
            markets_with_bets += 1
            all_bet_results.extend(bet_results)
        else:
            markets_skipped += 1
    
    # Calculate aggregated statistics
    total_bets = len(all_bet_results)
    winning_bets = sum(1 for b in all_bet_results if b.profit_loss > 0)
    losing_bets = sum(1 for b in all_bet_results if b.profit_loss < 0)
    total_staked = sum(b.stake for b in all_bet_results)
    total_liability = sum(b.liability for b in all_bet_results)
    net_pnl = sum(b.profit_loss for b in all_bet_results)
    win_rate = (winning_bets / total_bets * 100) if total_bets > 0 else 0.0
    
    # Break down by rule
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
    
    return BacktestSummary(
        total_markets=markets_processed,
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
