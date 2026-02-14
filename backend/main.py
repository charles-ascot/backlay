"""
CHIMERA Backtest Simulator — API Server
========================================
FastAPI backend for historical data backtesting.
Frontend served from Cloudflare Pages.
"""

import os
import logging
from typing import List
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backtester.orchestrator import BacktestOrchestrator
from backtester.strategy.rule_based import RuleBasedStrategy

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("backtest")

app = FastAPI(title="CHIMERA Backtest Simulator", version="2.0.0")

# ── CORS: Allow Cloudflare Pages frontend + local dev ──
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://backtest.thync.online")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "backtest-simulator"}


@app.post("/api/backtest/run")
async def run_backtest_simulation(
    files: List[UploadFile] = File(...),
    minutes_before: int = Form(...)
):
    """
    Run backtest simulation on uploaded historical stream files.

    Args:
        files: List of NDJSON stream files (one per market)
        minutes_before: Time offset before race to place bets (e.g., 30 = 30 min)

    Returns:
        Detailed results with P&L breakdown
    """
    if not files:
        return JSONResponse(
            status_code=400,
            content={"error": "No files uploaded"}
        )

    logger.info(f"Received {len(files)} file(s) for backtest at {minutes_before}min before race")

    # Read file contents
    market_files = []
    for file in files:
        try:
            content = await file.read()
            content_str = content.decode('utf-8')
            market_files.append((file.filename, content_str))
        except Exception as e:
            logger.error(f"Failed to read file {file.filename}: {e}")
            continue

    if not market_files:
        return JSONResponse(
            status_code=400,
            content={"error": "Failed to read any files"}
        )

    # Run backtest via orchestrator
    try:
        orchestrator = BacktestOrchestrator()
        report = orchestrator.run(market_files, minutes_before)
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"Backtest failed: {str(e)}"}
        )

    # Format results for frontend (preserving exact API contract)
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

    # Format rule breakdown
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
        "minutes_before_race": minutes_before,
    }


@app.get("/api/rules")
def get_rules():
    """Return the active rule set from the loaded strategy."""
    strategy = RuleBasedStrategy.default()
    config = strategy.config

    # Format rules for display
    rules_display = []
    for rule in config.get("rules", []):
        conditions_desc = " AND ".join(
            f"{c['field']} {c['operator']} {c['value']}"
            for c in rule.get("conditions", [])
        )
        actions_desc = ", ".join(
            f"{a['bet_type']} {a['target']} @ £{a['stake']}"
            for a in rule.get("actions", [])
        )
        rules_display.append({
            "id": rule["id"],
            "condition": conditions_desc,
            "action": actions_desc,
        })

    return {
        "strategy": config.get("id", "unknown"),
        "name": config.get("name", "Unknown"),
        "version": config.get("version", "0.0"),
        "markets": config.get("market_filters", {}),
        "rules": rules_display,
    }
