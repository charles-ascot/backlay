"""Replay engine models — enriched snapshots with computed fields."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class RunnerSnapshot:
    """A single runner's state at a point in time."""
    selection_id: int
    runner_name: str
    best_lay_price: Optional[float] = None
    status: str = "ACTIVE"


@dataclass
class EnrichedSnapshot:
    """Market snapshot enriched with computed strategy-relevant fields.

    This is what strategies receive. All computed fields are derived
    deterministically from the raw snapshot data.
    """
    # Identity
    market_id: str
    market_name: str
    venue: str
    market_time: str               # ISO format
    country_code: str
    market_type: str
    event_type_id: str

    # Timing
    publish_time: int              # Unix ms
    market_status: str
    in_play: bool

    # Runners (all runners from snapshot)
    runners: List[RunnerSnapshot] = field(default_factory=list)

    # Computed fields (set by replay engine)
    favourite: Optional[RunnerSnapshot] = None
    second_favourite: Optional[RunnerSnapshot] = None
    fav_lay_odds: Optional[float] = None
    second_lay_odds: Optional[float] = None
    gap_to_second: Optional[float] = None

    # Settlement (attached by orchestrator for simulation)
    settlement: Optional[Dict[int, str]] = None
