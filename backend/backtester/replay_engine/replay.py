"""
Market Replay Engine — Converts raw data into enriched snapshots.
=================================================================
Responsible for:
1. Finding the correct snapshot at the requested time offset
2. Enriching raw snapshots with computed fields (fav, 2nd fav, gap)
3. Attaching market metadata to the snapshot

No betting logic here — only market state reconstruction.
"""

from typing import Optional, List, Tuple

from backtester.data_layer.models import MarketData, RawMarketSnapshot
from backtester.data_layer.stream_parser import find_snapshot_at_offset
from backtester.replay_engine.models import EnrichedSnapshot, RunnerSnapshot


class MarketReplayEngine:
    """Replays market data and produces enriched snapshots at specific time offsets."""

    def get_snapshot_at_offset(
        self,
        market_data: MarketData,
        minutes_before_race: int,
    ) -> Optional[EnrichedSnapshot]:
        """Get an enriched snapshot at X minutes before race.

        Returns None if no suitable snapshot found.
        Delegates time-offset logic to data_layer.find_snapshot_at_offset,
        then enriches the result.
        """
        raw_snapshot = find_snapshot_at_offset(market_data, minutes_before_race)
        if raw_snapshot is None:
            return None

        return self._enrich_snapshot(raw_snapshot, market_data)

    def _enrich_snapshot(
        self,
        raw: RawMarketSnapshot,
        market_data: MarketData,
    ) -> EnrichedSnapshot:
        """Convert a RawMarketSnapshot + MarketData into an EnrichedSnapshot.

        Computes:
        - favourite (lowest lay price active runner)
        - second_favourite
        - fav_lay_odds
        - second_lay_odds
        - gap_to_second (second_lay_odds - fav_lay_odds)
        """
        # Convert raw runner dicts to RunnerSnapshot objects
        runners = []
        for r in raw.runners:
            runners.append(RunnerSnapshot(
                selection_id=r['selection_id'],
                runner_name=r['runner_name'],
                best_lay_price=r['best_lay_price'],
                status='ACTIVE',
            ))

        # Identify favourites
        favourite, second_favourite = self._identify_favourites(runners)

        # Compute derived fields
        fav_lay_odds = None
        second_lay_odds = None
        gap_to_second = None

        if favourite and favourite.best_lay_price is not None:
            fav_lay_odds = favourite.best_lay_price

        if second_favourite and second_favourite.best_lay_price is not None:
            second_lay_odds = second_favourite.best_lay_price

        if fav_lay_odds is not None and second_lay_odds is not None:
            gap_to_second = second_lay_odds - fav_lay_odds

        return EnrichedSnapshot(
            # Identity
            market_id=market_data.market_id,
            market_name=market_data.market_name,
            venue=market_data.venue,
            market_time=market_data.market_time,
            country_code=market_data.country_code,
            market_type=market_data.market_type,
            event_type_id=market_data.event_type_id,
            # Timing
            publish_time=raw.publish_time,
            market_status=raw.market_status,
            in_play=raw.in_play,
            # Runners
            runners=runners,
            # Computed
            favourite=favourite,
            second_favourite=second_favourite,
            fav_lay_odds=fav_lay_odds,
            second_lay_odds=second_lay_odds,
            gap_to_second=gap_to_second,
        )

    def _identify_favourites(
        self,
        runners: List[RunnerSnapshot],
    ) -> Tuple[Optional[RunnerSnapshot], Optional[RunnerSnapshot]]:
        """Identify favourite and second favourite from runner list.

        Favourite = runner with lowest lay odds (best_lay_price).
        Only considers ACTIVE runners with available lay prices.

        Logic preserved from rules.identify_favourites().
        """
        active = [
            r for r in runners
            if r.status == "ACTIVE" and r.best_lay_price is not None
        ]

        if len(active) < 1:
            return None, None

        # Sort by best lay price (lowest = favourite)
        active.sort(key=lambda r: r.best_lay_price)

        favourite = active[0]
        second_favourite = active[1] if len(active) > 1 else None

        return favourite, second_favourite
