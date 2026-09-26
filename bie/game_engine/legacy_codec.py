"""Strict, bounded I/O for the preserved canonical v1 contract.

This module never routes a legacy document into the v2 compiler implicitly.
"""
from dataclasses import MISSING, asdict, fields, is_dataclass
from pathlib import Path
from typing import Any, Union, get_args, get_origin, get_type_hints
import hashlib
import json
import math

from . import contracts as legacy
from .canonical import canonical_json
from .errors import GameContractError

LEGACY_CONTRACT_SHA256 = 'c3d6dabba6a1b4ff172d8ce7ada10d21d8911206cf45b11e4a3e4ff2e57e5b05'
MAX_WIRE_BYTES = 2_000_000

def verify_contract_seal():
    if hashlib.sha256(Path(legacy.__file__).read_bytes()).hexdigest() != LEGACY_CONTRACT_SHA256:
        raise GameContractError('GAME_LEGACY_CONTRACT_SEAL')

def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise GameContractError('GAME_LEGACY_DUPLICATE_JSON_KEY', key)
        result[key] = value
    return result

def _bounded(value, depth=0, budget=None):
    budget = [100_000] if budget is None else budget
    budget[0] -= 1
    if depth > 32 or budget[0] < 0:
        raise GameContractError('GAME_LEGACY_COMPLEXITY_LIMIT')
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                raise GameContractError('GAME_LEGACY_KEY_TYPE')
            _bounded(key, depth + 1, budget)
            _bounded(child, depth + 1, budget)
    elif type(value) is list:
        for child in value:
            _bounded(child, depth + 1, budget)
    elif type(value) is float:
        if not math.isfinite(value):
            raise GameContractError('GAME_LEGACY_NONFINITE')
    elif type(value) is str:
        try:
            value.encode('utf-8')
        except UnicodeError as exc:
            raise GameContractError('GAME_LEGACY_UNICODE') from exc
    elif value is not None and type(value) not in (str, int, bool):
        raise GameContractError('GAME_LEGACY_JSON_TYPE')

def _construct(cls, value, path='$'):
    origin, args = get_origin(cls), get_args(cls)
    if cls is Any:
        return value
    if origin is Union:
        if value is None and type(None) in args:
            return None
        for choice in args:
            if choice is type(None):
                continue
            try:
                return _construct(choice, value, path)
            except GameContractError:
                pass
        raise GameContractError('GAME_LEGACY_FIELD_TYPE', path)
    if origin is list:
        if type(value) is not list:
            raise GameContractError('GAME_LEGACY_FIELD_TYPE', path)
        return [_construct(args[0], child, path + '/' + str(i)) for i, child in enumerate(value)]
    if origin is dict:
        if type(value) is not dict:
            raise GameContractError('GAME_LEGACY_FIELD_TYPE', path)
        return {_construct(args[0], key, path): _construct(args[1], child, path + '/' + key)
                for key, child in value.items()}
    if is_dataclass(cls):
        if type(value) is not dict:
            raise GameContractError('GAME_LEGACY_FIELD_TYPE', path)
        specs = {f.name: f for f in fields(cls)}
        if set(value) - set(specs):
            raise GameContractError('GAME_LEGACY_UNKNOWN_FIELD', path)
        required = {name for name, f in specs.items() if f.default is MISSING and f.default_factory is MISSING}
        if required - set(value):
            raise GameContractError('GAME_LEGACY_REQUIRED_FIELD', path)
        hints = get_type_hints(cls)
        return cls(**{key: _construct(hints[key], child, path + '/' + key) for key, child in value.items()})
    if cls is float and type(value) in (int, float):
        return value  # preserve integer versus floating wire representation
    if type(value) is not cls:
        raise GameContractError('GAME_LEGACY_FIELD_TYPE', path)
    return value

def load_legacy(data):
    verify_contract_seal()
    if type(data) not in (bytes, str):
        raise GameContractError('GAME_LEGACY_WIRE_TYPE')
    try:
        wire = data.encode('utf-8') if type(data) is str else data
    except UnicodeError as exc:
        raise GameContractError('GAME_LEGACY_UNICODE') from exc
    if len(wire) > MAX_WIRE_BYTES:
        raise GameContractError('GAME_LEGACY_WIRE_LIMIT')
    try:
        raw = json.loads(wire, object_pairs_hook=_pairs)
        _bounded(raw)
    except (ValueError, RecursionError, UnicodeError) as exc:
        if isinstance(exc, GameContractError):
            raise
        raise GameContractError('GAME_LEGACY_JSON') from exc
    result = _construct(legacy.GameDocument, raw)
    if result.game_ir_version != '1.0.0':
        raise GameContractError('GAME_LEGACY_VERSION')
    try:
        result.validate()
    except legacy.GameIRContractError as exc:
        raise GameContractError('GAME_LEGACY_CONTRACT', str(exc)) from exc
    if len({e.game_id for e in result.experiences}) != len(result.experiences):
        raise GameContractError('GAME_LEGACY_DUPLICATE_EXPERIENCE')
    return result

def dump_legacy(document):
    if type(document) is not legacy.GameDocument:
        raise GameContractError('GAME_LEGACY_DOCUMENT_TYPE')
    raw = asdict(document)
    _bounded(raw)
    wire = canonical_json(raw)
    load_legacy(wire)
    return wire
