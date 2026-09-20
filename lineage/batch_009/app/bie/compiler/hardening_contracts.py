"""Bounded, explicit numeric/text contracts shared by COMP H1 emitters."""
from __future__ import annotations
import json
import math
from .element_compiler_common import ElementCompilerError

MAX_ITEMS = 2000
MAX_ABS_NUMBER = 1e100

def reject(code: str, message: str) -> None:
    raise ElementCompilerError(code + ": " + message)

def finite_number(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        reject("NUMERIC_VALUE_INVALID", name + " must be a JSON number, not a coerced string or boolean")
    try:
        result = float(value)
    except (ValueError, OverflowError):
        reject("NUMERIC_VALUE_INVALID", name + " is outside supported finite range")
    if not math.isfinite(result) or abs(result) > MAX_ABS_NUMBER:
        reject("NUMERIC_VALUE_INVALID", name + " must be finite with magnitude <= 1e100")
    return result

def sequence(value, name: str, *, minimum: int = 1, maximum: int = MAX_ITEMS):
    if not isinstance(value, (list, tuple)) or not minimum <= len(value) <= maximum:
        reject("COLLECTION_SHAPE_INVALID", f"{name} must contain {minimum}..{maximum} entries")
    return list(value)

def text_value(value, name: str, *, maximum: int = 100000, nonempty: bool = True) -> str:
    if not isinstance(value, str) or (nonempty and not value) or len(value) > maximum:
        reject("TEXT_VALUE_INVALID", name + " must be bounded text")
    try:
        value.encode("utf-8", "strict")
    except UnicodeEncodeError:
        reject("TEXT_VALUE_INVALID", name + " contains an unpaired Unicode surrogate")
    return value

def literal_child(value: str) -> str:
    """A JSX expression containing one JSON string, never raw JSX input."""
    text_value(value, "literal")
    return "{" + json.dumps(value, ensure_ascii=True, allow_nan=False) + "}"

def label(props: dict, key: str, default: str = "") -> str:
    return text_value(props.get(key, default), key, maximum=512, nonempty=False)
