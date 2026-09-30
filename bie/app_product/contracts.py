from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
import re

MAX_SOURCE_BYTES = 25 * 1024 * 1024
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)


class ProductContractError(ValueError):
    pass


@dataclass(frozen=True)
class SourceValidation:
    valid: bool
    source_sha256: str
    byte_length: int
    media_type: str
    issues: tuple[str, ...]
    schema_version: str = "bie.app.source-validation/1"

    def to_safe_dict(self) -> dict[str, object]:
        return asdict(self)


def validate_pdf_source(
    data: bytes,
    *,
    media_type: str = "application/pdf",
    max_bytes: int = MAX_SOURCE_BYTES,
) -> SourceValidation:
    if type(data) is not bytes:
        raise ProductContractError("source_bytes_required")
    if type(media_type) is not str or not media_type:
        raise ProductContractError("media_type_required")
    if type(max_bytes) is not int or max_bytes < 1:
        raise ProductContractError("invalid_source_limit")

    issues: list[str] = []
    if media_type.split(";", 1)[0].strip().lower() != "application/pdf":
        issues.append("unsupported_media_type")
    if not data:
        issues.append("empty_source")
    elif len(data) > max_bytes:
        issues.append("source_too_large")
    elif not data.startswith(b"%PDF-"):
        issues.append("pdf_signature_missing")

    digest = hashlib.sha256(data).hexdigest()
    return SourceValidation(
        valid=not issues,
        source_sha256=digest,
        byte_length=len(data),
        media_type="application/pdf",
        issues=tuple(issues),
    )


def require_sha256(value: str) -> str:
    if type(value) is not str or SHA256_PATTERN.fullmatch(value) is None:
        raise ProductContractError("invalid_sha256")
    return value


def require_identifier(value: str, field: str, *, max_length: int = 256) -> str:
    if type(value) is not str:
        raise ProductContractError(field + "_required")
    value = value.strip()
    if not value or len(value) > max_length:
        raise ProductContractError("invalid_" + field)
    if any(ord(ch) < 32 for ch in value):
        raise ProductContractError("invalid_" + field)
    return value
