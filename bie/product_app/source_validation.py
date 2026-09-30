"""Bounded source validation for the Section 18 operator surface."""
from __future__ import annotations
from pathlib import PurePath
import hashlib
import re

MAX_SOURCE_BYTES = 25 * 1024 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")

class SourceValidationError(ValueError):
    pass

def _safe_filename(filename: str) -> bool:
    if type(filename) is not str or not filename or len(filename) > 255:
        return False
    if filename != PurePath(filename).name or "/" in filename or "\\" in filename:
        return False
    if filename in {".", ".."} or "\x00" in filename:
        return False
    return True

def validate_pdf_source(filename: str, media_type: str, payload: bytes, *, max_bytes: int = MAX_SOURCE_BYTES) -> dict:
    """Return deterministic UI-safe validation; rejected bytes are never stored here."""
    errors=[]
    if type(max_bytes) is not int or isinstance(max_bytes,bool) or max_bytes < 1:
        raise SourceValidationError("invalid source byte limit")
    if not _safe_filename(filename): errors.append("unsafe_filename")
    if media_type != "application/pdf": errors.append("unsupported_media_type")
    if type(payload) is not bytes:
        errors.append("payload_must_be_bytes"); data=b""
    else:
        data=payload
        if not data: errors.append("empty_source")
        if len(data)>max_bytes: errors.append("source_too_large")
        if data and not data.startswith(b"%PDF-"): errors.append("invalid_pdf_magic")
    digest=hashlib.sha256(data).hexdigest()
    if not _SHA256.fullmatch(digest): raise AssertionError("sha256 invariant")
    return {
        "schema_version":"bie.app.source-validation/1",
        "filename":filename if _safe_filename(filename) else "",
        "media_type":media_type if type(media_type) is str else "",
        "size_bytes":len(data),"sha256":digest,
        "status":"VALID" if not errors else "INVALID","errors":errors,
        "product_accepted":False,
    }
