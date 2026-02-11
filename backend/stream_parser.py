"""
Stream Parser - Parse Betfair Historical Stream NDJSON Files
=============================================================
Handles the NDJSON format from Betfair historical data downloads.
Extracts market definitions, price snapshots, and settlement results.
"""

import json
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass
class MarketSnapshot:
    """A point-in-time snapshot of market prices."""
    market_id: str
    publish_time: int  # Unix ms
    runners: List[Dict]  # {selection_id, runner_name, best_lay_price}
    market_status: str
    in_play: bool


@dataclass
class MarketData:
    """Complete market data parsed from stream file."""
    market_id: str
    market_name: str
    venue: str
    market_time: str  # ISO format
    event_type_id: str
    country_code: str
    market_type: str
    runners_metadata: Dict[int, str]  # {selection_id: runner_name}
    snapshots: List[MarketSnapshot]
    settlement: Optional[Dict[int, str]]  # {selection_id: 'WINNER' | 'LOSER'}
    
    
def parse_stream_file(file_content: str) -> Optional[MarketData]:
    """
    Parse a single NDJSON stream file.
    Returns MarketData with all snapshots and settlement.
    """
    lines = file_content.strip().split('\n')
    if not lines:
        return None
    
    market_id = None
    market_name = None
    venue = None
    market_time = None
    event_type_id = None
    country_code = None
    market_type = None
    runners_metadata = {}
    snapshots = []
    settlement = None
    
    # Track current runner prices (delta updates)
    current_prices = {}  # {selection_id: {batl: [[level, price, size], ...]}}
    
    for line in lines:
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
            
        if msg.get('op') != 'mcm':
            continue
            
        pt = msg.get('pt', 0)
        mc = msg.get('mc', [])
        
        for market_change in mc:
            if not market_id:
                market_id = market_change.get('id')
            
            # Extract market definition (metadata + runner names)
            market_def = market_change.get('marketDefinition')
            if market_def:
                market_name = market_def.get('name', '')
                venue = market_def.get('venue', 'Unknown')
                market_time = market_def.get('marketTime', '')
                event_type_id = market_def.get('eventTypeId', '')
                country_code = market_def.get('countryCode', '')
                market_type = market_def.get('marketType', '')
                
                # Extract runner names
                for runner in market_def.get('runners', []):
                    sel_id = runner.get('id')
                    name = runner.get('name', f'Runner {sel_id}')
                    runners_metadata[sel_id] = name
                    
                # Check for settlement
                status = market_def.get('status')
                if status == 'CLOSED':
                    settlement = {}
                    for runner in market_def.get('runners', []):
                        sel_id = runner.get('id')
                        runner_status = runner.get('status', 'ACTIVE')
                        settlement[sel_id] = runner_status
            
            # Extract price updates
            rc = market_change.get('rc', [])
            for runner_change in rc:
                sel_id = runner_change.get('id')
                
                # Update current prices with delta
                if sel_id not in current_prices:
                    current_prices[sel_id] = {}
                
                # Best available to lay (batl)
                batl = runner_change.get('batl')
                if batl is not None:
                    current_prices[sel_id]['batl'] = batl
            
            # Create snapshot if we have price data
            if current_prices:
                runners = []
                for sel_id, prices in current_prices.items():
                    batl = prices.get('batl', [])
                    best_lay = None
                    if batl and len(batl) > 0:
                        # batl format: [[level, price, size], ...]
                        # Level 0 = best price
                        best_lay = batl[0][1] if len(batl[0]) > 1 else None
                    
                    runners.append({
                        'selection_id': sel_id,
                        'runner_name': runners_metadata.get(sel_id, f'Runner {sel_id}'),
                        'best_lay_price': best_lay,
                    })
                
                snapshot = MarketSnapshot(
                    market_id=market_id,
                    publish_time=pt,
                    runners=runners,
                    market_status=market_def.get('status', 'OPEN') if market_def else 'OPEN',
                    in_play=market_def.get('inPlay', False) if market_def else False,
                )
                snapshots.append(snapshot)
    
    if not market_id:
        return None
    
    return MarketData(
        market_id=market_id,
        market_name=market_name or 'Unknown',
        venue=venue or 'Unknown',
        market_time=market_time or '',
        event_type_id=event_type_id or '',
        country_code=country_code or '',
        market_type=market_type or '',
        runners_metadata=runners_metadata,
        snapshots=snapshots,
        settlement=settlement,
    )


def find_snapshot_at_offset(
    market_data: MarketData,
    minutes_before_race: int
) -> Optional[MarketSnapshot]:
    """
    Find the closest snapshot to X minutes before race time.
    Returns None if no suitable snapshot found.
    """
    if not market_data.market_time:
        return None
    
    try:
        race_time = datetime.fromisoformat(market_data.market_time.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None
    
    # Calculate target time
    target_ms = int((race_time.timestamp() - minutes_before_race * 60) * 1000)
    
    # Filter to pre-race snapshots only
    pre_race_snapshots = [
        s for s in market_data.snapshots
        if s.publish_time <= race_time.timestamp() * 1000 and not s.in_play
    ]
    
    if not pre_race_snapshots:
        return None
    
    # Find closest snapshot to target time
    closest = min(
        pre_race_snapshots,
        key=lambda s: abs(s.publish_time - target_ms)
    )
    
    return closest
