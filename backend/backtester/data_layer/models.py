"""Data layer models — raw parsed data from stream files."""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class RawMarketSnapshot:
    """A point-in-time snapshot of market prices, as parsed from NDJSON.

    This is the raw data structure before any enrichment.
    runners is a list of dicts: {selection_id: int, runner_name: str, best_lay_price: Optional[float]}
    """
    market_id: str
    publish_time: int          # Unix milliseconds
    runners: List[Dict]        # [{selection_id, runner_name, best_lay_price}, ...]
    market_status: str         # 'OPEN', 'SUSPENDED', 'CLOSED'
    in_play: bool


@dataclass
class MarketData:
    """Complete market data parsed from a single stream file."""
    market_id: str
    market_name: str
    venue: str
    market_time: str           # ISO format string
    event_type_id: str
    country_code: str
    market_type: str
    runners_metadata: Dict[int, str]   # {selection_id: runner_name}
    snapshots: List[RawMarketSnapshot]
    settlement: Optional[Dict[int, str]]  # {selection_id: 'WINNER'|'LOSER'|'REMOVED'}
