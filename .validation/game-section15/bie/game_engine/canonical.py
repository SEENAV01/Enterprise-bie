from __future__ import annotations
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any
import hashlib, json, math
from .errors import GameContractError

def _plain(value: Any):
    if is_dataclass(value): return _plain(asdict(value))
    if isinstance(value, Enum): return value.value
    if isinstance(value, dict): return {str(k):_plain(value[k]) for k in sorted(value)}
    if isinstance(value, (list,tuple)): return [_plain(x) for x in value]
    if isinstance(value, (set,frozenset)): return sorted(_plain(x) for x in value)
    if isinstance(value, Path): return value.as_posix()
    if isinstance(value, float) and not math.isfinite(value): raise GameContractError('GAME_CANONICAL_NONFINITE')
    if value is None or isinstance(value,(str,int,float,bool)): return value
    raise GameContractError('GAME_CANONICAL_UNSUPPORTED_TYPE',type(value).__name__)

def canonical_json(value: Any) -> bytes:
    try:return json.dumps(_plain(value),sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')
    except (TypeError,ValueError) as e: raise GameContractError('GAME_CANONICAL_JSON') from e

def fingerprint(value: Any) -> str:
    return 'sha256:'+hashlib.sha256(canonical_json(value)).hexdigest()
