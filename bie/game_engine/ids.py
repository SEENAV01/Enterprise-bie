from __future__ import annotations
import re
from .errors import GameContractError

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")

def require_id(value: str, code: str="GAME_ID_INVALID") -> str:
    if type(value) is not str or not _ID.fullmatch(value): raise GameContractError(code)
    return value


def require_text(value: str, code: str="GAME_TEXT_INVALID", *, max_length: int=2000) -> str:
    if type(value) is not str or not value.strip() or len(value)>max_length or any(ord(c)<32 and c not in "\n\t" for c in value):
        raise GameContractError(code)
    return value

def require_sha256(value: str, code: str="GAME_SHA256_INVALID") -> str:
    if type(value) is not str or not _SHA.fullmatch(value): raise GameContractError(code)
    return value

def require_semver(value: str, code: str="GAME_SEMVER_INVALID") -> str:
    if type(value) is not str or not _SEMVER.fullmatch(value): raise GameContractError(code)
    return value

def require_unique_ids(values, code="GAME_DUPLICATE_ID"):
    values=tuple(values)
    if len(values)!=len(set(values)): raise GameContractError(code)
    return values
