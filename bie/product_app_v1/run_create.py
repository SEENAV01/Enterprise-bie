from __future__ import annotations

from .models import CREATE_KEY_RE, OperatorError
from .store import SQLiteOperatorStore


def create_run(store: SQLiteOperatorStore, create_key: str) -> dict[str, object]:
    """Create or idempotently recover a durable product run identity."""
    if type(create_key) is not str or not CREATE_KEY_RE.fullmatch(create_key):
        raise OperatorError("invalid_create_key")
    return store.create_run(create_key).to_safe_dict()
