"""GCS bucket discovery — stub for future implementation."""

from typing import List


class GCSDiscovery:
    """Discovers and lists available market data files in GCS buckets.

    Future implementation will:
    - Recursively scan GCS bucket
    - Detect NDJSON files (.json, .ndjson, .gz)
    - Detect format from file content, not path
    - Extract market_id dynamically
    - Group files per market
    """

    def __init__(self, bucket_name: str = "", prefix: str = ""):
        self.bucket_name = bucket_name
        self.prefix = prefix

    def list_market_files(
        self,
        date_from: str = "",
        date_to: str = "",
        country_codes: List[str] = None,
    ) -> List[str]:
        """List available market file paths in the bucket.

        Returns list of GCS object paths.
        """
        raise NotImplementedError("GCS discovery not yet implemented")

    def download_file(self, gcs_path: str) -> str:
        """Download a single file and return its contents as a string."""
        raise NotImplementedError("GCS discovery not yet implemented")
