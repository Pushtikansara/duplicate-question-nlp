from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path

from ares.api.config import APIConfig
from ares.api.exceptions import ValidationError

logger = logging.getLogger(__name__)


class UploadManager:
    def __init__(self) -> None:
        self._config = APIConfig.get()
        self._upload_dir = Path(self._config.upload_dir)
        self._max_size = self._config.max_upload_size_mb * 1024 * 1024

    def ensure_upload_dir(self) -> Path:
        self._upload_dir.mkdir(parents=True, exist_ok=True)
        return self._upload_dir

    async def save_upload(self, filename: str, content: bytes) -> Path:
        if len(content) > self._max_size:
            raise ValidationError(detail=f"Upload exceeds maximum size of {self._config.max_upload_size_mb}MB")
        ext = Path(filename).suffix
        safe_name = f"{uuid.uuid4().hex}{ext}"
        filepath = self.ensure_upload_dir() / safe_name
        with open(filepath, "wb") as f:
            f.write(content)
        logger.info("Saved upload: %s -> %s (%d bytes)", filename, filepath, len(content))
        return filepath

    def cleanup(self, max_age_hours: int = 24) -> int:
        now = time.time()
        cutoff = now - (max_age_hours * 3600)
        removed = 0
        for f in self._upload_dir.iterdir():
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink()
                removed += 1
        return removed


_upload_manager: UploadManager | None = None


def get_upload_manager() -> UploadManager:
    global _upload_manager
    if _upload_manager is None:
        _upload_manager = UploadManager()
    return _upload_manager
