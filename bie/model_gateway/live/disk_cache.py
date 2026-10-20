"""Content-addressed response cache on disk.

The key covers provider, model, messages, schema, temperature and prompt version, so a changed
prompt or schema never reuses an old answer. Only validated responses are stored. Keys and
secrets are never part of the cache key or the stored value.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def cache_key(**parts) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                                     default=str).encode("utf-8")).hexdigest()


class DiskCache:
    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        if len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
            raise ValueError("cache key must be a sha256 hex digest")
        return self.directory / key[:2] / (key + ".json")

    def get(self, key: str):
        path = self._path(key)
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return value if isinstance(value, dict) and value.get("key") == key else None

    def put(self, key: str, value: dict):
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(f".{os.getpid()}.tmp")
        temp.write_text(json.dumps({**value, "key": key}, sort_keys=True, ensure_ascii=False), encoding="utf-8")
        os.replace(temp, path)
