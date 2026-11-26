"""Logging, integrity and artifact helpers."""

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import numpy as np


def now() -> str:
    return datetime.now(UTC).isoformat()


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps(
            {"time": now(), "level": record.levelname, "message": record.getMessage()}
        )


def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_write(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)

    def normalize(value):
        if isinstance(value, dict):
            return {str(k): normalize(v) for k, v in value.items()}
        if isinstance(value, (tuple, list, np.ndarray)):
            return [normalize(v) for v in value]
        if isinstance(value, (np.integer, np.floating, np.bool_)):
            value = value.item()
        if isinstance(value, float) and not np.isfinite(value):
            return None
        if isinstance(value, Path):
            return str(value)
        return value

    path.write_text(json.dumps(normalize(obj), indent=2, allow_nan=False), encoding="utf-8")
