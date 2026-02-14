"""GCS bucket discovery — scan, detect, and download market data files."""

import bz2
import gzip
import json
import logging
from typing import List, Tuple, Optional

from google.cloud import storage
from google.api_core import exceptions as gcs_exceptions

logger = logging.getLogger("backtest.gcs_discovery")

# Supported file extensions for detection
SUPPORTED_EXTENSIONS = {".json", ".ndjson", ".gz", ".bz2"}


class GCSDiscovery:
    """Discovers and downloads market data files from GCS buckets.

    Responsibilities (MODULE 1 — DATA DISCOVERY):
    - Recursively scan GCS bucket under a prefix
    - Detect NDJSON files (.json, .ndjson, .gz)
    - Detect format from file content, not path
    - Extract market_id dynamically from file content
    - Group files per market
    - No strategy logic
    """

    def __init__(self, bucket_name: str, prefix: str = ""):
        self.bucket_name = bucket_name
        self.prefix = prefix.strip("/")
        self._client = storage.Client()  # Uses ADC on Cloud Run
        self._bucket = self._client.bucket(bucket_name)

    @classmethod
    def from_gcs_url(cls, gcs_url: str) -> "GCSDiscovery":
        """Parse a gs://bucket/prefix URL into a GCSDiscovery instance.

        Accepts formats:
            gs://my-bucket
            gs://my-bucket/
            gs://my-bucket/some/prefix/
            gs://my-bucket/some/prefix
        """
        if not gcs_url.startswith("gs://"):
            raise ValueError(
                f"Invalid GCS URL: must start with gs:// (got: {gcs_url})"
            )
        path = gcs_url[5:]  # strip "gs://"
        parts = path.split("/", 1)
        bucket_name = parts[0]
        prefix = parts[1] if len(parts) > 1 else ""
        if not bucket_name:
            raise ValueError("Invalid GCS URL: bucket name is empty")
        return cls(bucket_name=bucket_name, prefix=prefix)

    def list_market_files(self) -> List[str]:
        """Recursively list all potential market data files in the bucket.

        Returns list of GCS blob names (object paths) with supported
        extensions. The recursive scan is handled by GCS's prefix-based
        listing (no delimiter = recursive).
        """
        prefix = self.prefix + "/" if self.prefix else ""
        blobs = self._client.list_blobs(self._bucket, prefix=prefix)

        file_paths = []
        for blob in blobs:
            # Skip "directory" markers (zero-byte objects ending in /)
            if blob.name.endswith("/"):
                continue
            # Check extension
            name_lower = blob.name.lower()
            if any(name_lower.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                file_paths.append(blob.name)

        logger.info(
            f"Found {len(file_paths)} candidate files in "
            f"gs://{self.bucket_name}/{prefix}"
        )
        return file_paths

    def download_file(self, blob_name: str) -> str:
        """Download a single file and return contents as a UTF-8 string.

        Handles .gz decompression transparently.
        """
        blob = self._bucket.blob(blob_name)
        raw_bytes = blob.download_as_bytes()

        # Decompress if compressed
        if blob_name.lower().endswith(".gz"):
            raw_bytes = gzip.decompress(raw_bytes)
        elif blob_name.lower().endswith(".bz2"):
            raw_bytes = bz2.decompress(raw_bytes)

        return raw_bytes.decode("utf-8")

    def is_ndjson_content(self, content: str) -> bool:
        """Detect if content is valid NDJSON with Betfair stream data.

        Format detection from content, not path — per MODULE 1 spec.
        Checks that at least one line parses as JSON with an 'op' field.
        """
        for line in content.split("\n", 5):  # Check first few lines
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                if isinstance(msg, dict) and "op" in msg:
                    return True
            except json.JSONDecodeError:
                continue
        return False

    def extract_market_id(self, content: str) -> Optional[str]:
        """Extract market_id from file content dynamically.

        Looks for the first mcm message containing a market change with an id.
        """
        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if msg.get("op") == "mcm":
                for mc in msg.get("mc", []):
                    market_id = mc.get("id")
                    if market_id:
                        return market_id
        return None

    def discover_and_download(self) -> List[Tuple[str, str]]:
        """Full discovery pipeline: scan, download, validate, return.

        Returns:
            List of (blob_name, content_str) tuples — same format the
            orchestrator expects. Only includes files that are valid NDJSON
            with detectable market data.

        Also groups by market_id to deduplicate (if multiple files
        reference the same market, only the first is kept).
        """
        blob_names = self.list_market_files()
        if not blob_names:
            return []

        market_files = []
        seen_market_ids: set = set()
        skipped_invalid = 0
        skipped_duplicate = 0

        for blob_name in blob_names:
            try:
                content = self.download_file(blob_name)
            except Exception as e:
                logger.warning(f"Failed to download {blob_name}: {e}")
                continue

            # Content-based format detection
            if not self.is_ndjson_content(content):
                skipped_invalid += 1
                logger.debug(f"Skipped non-NDJSON file: {blob_name}")
                continue

            # Extract market_id for grouping/dedup
            market_id = self.extract_market_id(content)
            if market_id and market_id in seen_market_ids:
                skipped_duplicate += 1
                logger.debug(
                    f"Skipped duplicate market {market_id}: {blob_name}"
                )
                continue

            if market_id:
                seen_market_ids.add(market_id)

            market_files.append((blob_name, content))

        logger.info(
            f"Discovery complete: {len(market_files)} valid files, "
            f"{skipped_invalid} non-NDJSON skipped, "
            f"{skipped_duplicate} duplicates skipped"
        )
        return market_files
