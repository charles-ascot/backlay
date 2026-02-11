"""
CHIMERA Backtest Simulator - API Server
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

from backtest_engine import run_backtest

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("backtest")

app = FastAPI(title="CHIMERA Backtest Simulator", version="1.0.0")

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
    
    # Run backtest
    try:
        summary = run_backtest(market_files, minutes_before)
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"Backtest failed: {str(e)}"}
        )
    
    # Format results for frontend
    bet_results = []
    for bet in summary.bet_results:
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
    for rule, stats in summary.results_by_rule.items():
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
            "total_markets": summary.total_markets,
            "markets_with_bets": summary.markets_with_bets,
            "markets_skipped": summary.markets_skipped,
            "total_bets": summary.total_bets,
            "winning_bets": summary.winning_bets,
            "losing_bets": summary.losing_bets,
            "win_rate": summary.win_rate,
            "total_staked": summary.total_staked,
            "total_liability": summary.total_liability,
            "net_profit_loss": summary.net_profit_loss,
        },
        "bet_results": bet_results,
        "rules_breakdown": rules_breakdown,
        "minutes_before_race": minutes_before,
    }


@app.get("/api/rules")
def get_rules():
    """Return the active rule set."""
    return {
        "strategy": "UK_IE_Favourite_Lay",
        "version": "2.0",
        "timing": "pre_off",
        "markets": {
            "event_type": "7 (Horse Racing)",
            "countries": ["GB", "IE"],
            "market_type": "WIN",
        },
        "rules": [
            {
                "id": "RULE_1",
                "condition": "Favourite odds < 2.0",
                "action": "LAY favourite @ £3",
            },
            {
                "id": "RULE_2",
                "condition": "Favourite odds 2.0 – 5.0",
                "action": "LAY favourite @ £2",
            },
            {
                "id": "RULE_3A",
                "condition": "Favourite odds > 5.0 AND gap to 2nd favourite < 2",
                "action": "LAY favourite @ £1 + LAY 2nd favourite @ £1",
            },
            {
                "id": "RULE_3B",
                "condition": "Favourite odds > 5.0 AND gap to 2nd favourite ≥ 2",
                "action": "LAY favourite @ £1",
            },
        ],
    }
