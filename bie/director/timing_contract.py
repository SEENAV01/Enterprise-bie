"""Shared validated timing vocabulary, owned by BIE-DIR-TIME-001.

Integer milliseconds are used at API boundaries. Policies are engineering
heuristics, not calibrated comprehension or pronunciation models.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import re


def fingerprint(value):
    payload = asdict(value) if hasattr(value, "__dataclass_fields__") else value
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def nonblank(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonblank string")
    return value


def ordered(values, name):
    if isinstance(values, (str, bytes, set, frozenset, dict)):
        raise ValueError(f"{name} must be an ordered iterable")
    try:
        return tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an ordered iterable") from exc


def identifiers(values, name, allow_empty=False):
    result = ordered(values, name)
    if not allow_empty and not result:
        raise ValueError(f"{name} must not be empty")
    for value in result:
        nonblank(value, name)
    if len(set(result)) != len(result):
        raise ValueError(f"{name} contains duplicates")
    return result


def number(value, name, low=0.0, high=None, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite numeric data, not bool")
    if value < low or (positive and value <= 0) or (high is not None and value > high):
        raise ValueError(f"{name} outside allowed range")
    return value


def integer(value, name, low=0):
    if type(value) is not int or value < low:
        raise ValueError(f"{name} must be an integer >= {low}")
    return value


def digest_id(value, name):
    if not isinstance(value, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
        raise ValueError(f"{name} must be sha256:<64 lowercase hex digits>")
    return value


@dataclass(frozen=True)
class TimingPolicy:
    version: str = "bie-dir-timing/1.0.0"
    tokenizer: str = "unicode-word-runs/1"
    default_wpm: float = 150.0
    min_wpm: float = 80.0
    max_wpm: float = 200.0
    estimate_margin: float = 0.20

    def validate(self):
        nonblank(self.version, "policy version")
        if self.tokenizer != "unicode-word-runs/1":
            raise ValueError("unsupported tokenizer")
        number(self.min_wpm, "min_wpm", 1.0)
        number(self.max_wpm, "max_wpm", self.min_wpm, 1000.0)
        number(self.default_wpm, "default_wpm", self.min_wpm, self.max_wpm)
        number(self.estimate_margin, "estimate_margin", 0.0, 1.0)


@dataclass(frozen=True)
class SpokenWord:
    index: int
    text: str
    start_char: int
    end_char: int


def spoken_words(text):
    """Explicit lexical estimate; digits/math/non-English text require review."""
    nonblank(text, "realized narration text")
    words = tuple(SpokenWord(i, m.group(), m.start(), m.end()) for i, m in
                  enumerate(re.finditer(r"[^\W_]+(?:['’][^\W_]+)*", text)))
    if not words:
        raise ValueError("narration has no lexical words; supply spoken realization")
    return words


def text_review_reasons(text, language):
    reasons = []
    if language.split("-")[0].lower() != "en" or any(ord(c) > 127 and c not in "’“”–—…" for c in text):
        reasons.append("LANGUAGE_TOKENIZATION_UNCALIBRATED")
    if any(c.isdigit() for c in text) or any(c in "=+*/^<>_%\\" for c in text):
        reasons.append("NUMERIC_OR_SYMBOLIC_SPOKEN_REALIZATION_REQUIRED")
    return tuple(reasons)
