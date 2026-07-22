from __future__ import annotations

import gzip
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def compress(data: bytes) -> bytes:
    return gzip.compress(data)


def decompress(data: bytes) -> bytes:
    return gzip.decompress(data)


def should_compress(data: dict[str, Any]) -> bool:
    return len(json.dumps(data).encode()) > 1024 * 10
