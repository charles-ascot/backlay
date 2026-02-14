"""Data Layer — NDJSON parsing and data discovery."""

from backtester.data_layer.stream_parser import parse_stream_file, find_snapshot_at_offset
from backtester.data_layer.models import MarketData, RawMarketSnapshot

__all__ = ["parse_stream_file", "find_snapshot_at_offset", "MarketData", "RawMarketSnapshot"]
