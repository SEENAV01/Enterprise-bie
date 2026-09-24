"""Shared immutable AUDIO preparation contracts, owned by AUDIO-VO-001.

Content identities use the existing DIR canonical SHA-256 convention. These are
preparation records, not a replacement for the canonical BIE artifact catalogue.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass, is_dataclass
import json
import re
import unicodedata
from bie.director.timing_contract import fingerprint as _dir_fingerprint


def fingerprint(value: object) -> str:
    def plain(v):
        if is_dataclass(v):
            return plain(asdict(v))
        if type(v) in (tuple, list):
            return [plain(x) for x in v]
        if type(v) is dict:
            return {k: plain(x) for k, x in v.items()}
        return v
    return _dir_fingerprint(plain(value))


class AudioError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code, self.detail = code, detail
        super().__init__(f"{code}: {detail}" if detail else code)


def text(value: object, name: str, maximum: int = 100000) -> str:
    if type(value) is not str or not value.strip() or len(value) > maximum:
        raise AudioError("INVALID_TEXT", name)
    if any(0xD800 <= ord(c) <= 0xDFFF or (unicodedata.category(c) == "Cc" and c not in "\n\t\r") for c in value):
        raise AudioError("INVALID_UNICODE_OR_CONTROL", name)
    return value


def integer(value: object, name: str, low: int = 0, high: int = 10000000) -> int:
    if type(value) is not int or not low <= value <= high:
        raise AudioError("INVALID_INTEGER", name)
    return value


def refs(values: object, name: str, required: bool = True) -> tuple[str, ...]:
    if type(values) is not tuple or (required and not values) or len(values) > 4096:
        raise AudioError("INVALID_REFERENCES", name)
    for v in values:
        text(v, name, 2048)
    if len(set(values)) != len(values):
        raise AudioError("DUPLICATE_REFERENCE", name)
    return values


def locale(value: str) -> str:
    text(value, "language", 64)
    if not re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", value):
        raise AudioError("INVALID_LANGUAGE", value)
    return value


def digest(value: str) -> str:
    if type(value) is not str or not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
        raise AudioError("INVALID_DIGEST")
    return value


def is_word(c: str) -> bool:
    return bool(c) and (unicodedata.category(c)[0] in "LMN" or c in "_'’\u200c\u200d")


def boundary(s: str, i: int) -> bool:
    """Offsets are Unicode code points, not UTF-16 units. Never cut grapheme joins."""
    if not 0 <= i <= len(s):
        return False
    if i in (0, len(s)):
        return True
    return not (unicodedata.category(s[i]).startswith("M") or s[i] in "\u200c\u200d" or s[i-1] in "\u200c\u200d" or s[i-1:i+1] == "\r\n")


def exact_fields(row: object, keys: tuple[str, ...]) -> dict:
    if type(row) is not dict or set(row) != set(keys):
        raise AudioError("FIELDS_MISMATCH", ",".join(keys))
    return row


def strict_json(s: str) -> object:
    def pairs(rows):
        out = {}
        for k, v in rows:
            if k in out:
                raise AudioError("DUPLICATE_JSON_KEY", k)
            out[k] = v
        return out
    def bad(v):
        raise AudioError("NONFINITE_JSON", v)
    if len(s.encode("utf-8")) > 8_000_000:
        raise AudioError("JSON_BUDGET")
    try:
        out = json.loads(s, object_pairs_hook=pairs, parse_constant=bad)
        json.dumps(out, allow_nan=False)
        return out
    except (ValueError, TypeError, RecursionError) as exc:
        if isinstance(exc, AudioError):
            raise
        raise AudioError("INVALID_JSON", str(exc)[:160]) from exc


@dataclass(frozen=True)
class Reading:
    surface: str
    spoken: str
    language: str
    kind: str
    rule_id: str
    source_refs: tuple[str, ...]
    phonemes: str | None = None
    alphabet: str | None = None

    def __post_init__(self):
        text(self.surface, "surface", 8192)
        text(self.spoken, "spoken", 65536)
        locale(self.language)
        text(self.kind, "kind", 40)
        text(self.rule_id, "rule_id", 2048)
        refs(self.source_refs, "reading evidence")
        if (self.phonemes is None) != (self.alphabet is None):
            raise AudioError("PHONEME_ALPHABET_PAIR")
        if self.phonemes is not None:
            text(self.phonemes, "phonemes", 4096)
            if self.alphabet != "ipa":
                raise AudioError("UNSUPPORTED_PHONEME_ALPHABET")

    def fingerprint(self) -> str:
        return fingerprint(self)


# Versioned technical letter-name convention; not an acoustic model.
EN=("ay","bee","see","dee","ee","ef","gee","aitch","eye","jay","kay","el","em","en","oh","pee","cue","ar","ess","tee","you","vee","double you","ex","why","zee")
HI=("ए","बी","सी","डी","ई","एफ","जी","एच","आई","जे","के","एल","एम","एन","ओ","पी","क्यू","आर","एस","टी","यू","वी","डब्ल्यू","एक्स","वाई","ज़ेड")
