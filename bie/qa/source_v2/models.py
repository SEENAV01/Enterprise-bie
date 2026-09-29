"""Strict Section 16 source evidence; immutable records, explicit text offsets.

SHA-256 is identity, not truth. Offsets are Python Unicode code-point offsets
into the exact decoded UTF-8 string; no silent case/whitespace normalization.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
from ..release_v2.contracts import (
    ArtifactRef, ContractError, canonical_bytes, digest, token, integer,
    sha256, revision, choice, tuple_tokens,
)
VERSION = '1.0.0'
MAX_TEXT = 1_000_000
MAX_ITEMS = 4096
MAX_SOURCE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024


def text(value: Any, field: str, maximum: int = MAX_TEXT) -> str:
    if type(value) is not str or not value.strip() or len(value) > maximum:
        raise ContractError('INVALID_TEXT', field)
    try:
        value.encode('utf-8', errors='strict')
    except UnicodeError as exc:
        raise ContractError('INVALID_UNICODE', field) from exc
    if '\x00' in value:
        raise ContractError('NUL_IN_TEXT', field)
    return value


def records(value: Any, cls: type, field: str, key: str, minimum: int = 0) -> None:
    if type(value) is not tuple or not minimum <= len(value) <= MAX_ITEMS:
        raise ContractError('INVALID_RECORD_COLLECTION', field)
    if any(type(x) is not cls for x in value):
        raise ContractError('INVALID_RECORD_TYPE', field)
    if len({getattr(x, key) for x in value}) != len(value):
        raise ContractError('DUPLICATE_RECORD_ID', field)


@dataclass(frozen=True, slots=True)
class Source:
    source_id: str
    artifact: ArtifactRef
    media_type: str
    page_count: int

    def __post_init__(self):
        token(self.source_id, 'source_id')
        if type(self.artifact) is not ArtifactRef or self.artifact.role != 'source':
            raise ContractError('INVALID_SOURCE_ARTIFACT')
        choice(self.media_type, ('utf8', 'pdf', 'image', 'epub', 'docx', 'html'), 'media_type')
        integer(self.page_count, 'page_count', 1, 100_000)
        if self.media_type == 'utf8' and self.page_count != 1:
            raise ContractError('UTF8_REQUIRES_ONE_PAGE')
        if self.artifact.size > MAX_SOURCE_BYTES:
            raise ContractError('SOURCE_SIZE_LIMIT')


@dataclass(frozen=True, slots=True)
class Block:
    block_id: str
    source_id: str
    source_sha256: str
    page: int
    region_id: str
    box_ppm: tuple[int, int, int, int]
    text: str
    extractor_id: str
    extractor_version: str
    confidence_ppm: int

    def __post_init__(self):
        for field in ('block_id', 'source_id', 'region_id', 'extractor_id', 'extractor_version'):
            token(getattr(self, field), field)
        sha256(self.source_sha256, 'source_sha256')
        integer(self.page, 'page', 1, 100_000)
        text(self.text, 'block.text')
        integer(self.confidence_ppm, 'confidence_ppm', 0, 1_000_000)
        if type(self.box_ppm) is not tuple or len(self.box_ppm) != 4:
            raise ContractError('INVALID_BOX')
        for n in self.box_ppm:
            integer(n, 'box', 0, 1_000_000)
        a,b,c,d = self.box_ppm
        if not a < c or not b < d:
            raise ContractError('INVALID_BOX')

    @property
    def content_digest(self) -> str:
        return digest(asdict(self))


@dataclass(frozen=True, slots=True)
class Output:
    output_id: str
    artifact: ArtifactRef
    channel: str

    def __post_init__(self):
        token(self.output_id, 'output_id')
        if type(self.artifact) is not ArtifactRef or self.artifact.role != 'support':
            raise ContractError('INVALID_OUTPUT_ARTIFACT')
        choice(self.channel, ('narration', 'caption', 'on_screen', 'game_feedback',
                             'game_prompt', 'lesson'), 'channel')
        if self.artifact.size > MAX_TEXT * 4:
            raise ContractError('OUTPUT_SIZE_LIMIT')


@dataclass(frozen=True, slots=True)
class Citation:
    citation_id: str
    block_id: str
    block_digest: str
    start: int
    end: int
    quote: str

    def __post_init__(self):
        token(self.citation_id, 'citation_id'); token(self.block_id, 'block_id')
        sha256(self.block_digest, 'block_digest')
        integer(self.start, 'citation.start', 0, MAX_TEXT)
        integer(self.end, 'citation.end', self.start + 1, MAX_TEXT)
        text(self.quote, 'quote')


@dataclass(frozen=True, slots=True)
class Claim:
    claim_id: str
    output_id: str
    output_sha256: str
    start: int
    end: int
    text: str
    kind: str
    citation_ids: tuple[str, ...]

    def __post_init__(self):
        token(self.claim_id, 'claim_id'); token(self.output_id, 'output_id')
        sha256(self.output_sha256, 'output_sha256')
        integer(self.start, 'claim.start', 0, MAX_TEXT)
        integer(self.end, 'claim.end', self.start + 1, MAX_TEXT)
        text(self.text, 'claim.text')
        choice(self.kind, ('FACT', 'QUESTION', 'INSTRUCTION', 'OTHER'), 'kind')
        tuple_tokens(self.citation_ids, 'citation_ids', 0, 128)


@dataclass(frozen=True, slots=True)
class Request:
    schema_version: str
    run_id: str
    revision: str
    candidate_digest: str
    sources: tuple[Source, ...]
    blocks: tuple[Block, ...]
    outputs: tuple[Output, ...]
    citations: tuple[Citation, ...]
    claims: tuple[Claim, ...]

    def __post_init__(self):
        if self.schema_version != VERSION:
            raise ContractError('UNSUPPORTED_SOURCE_SCHEMA')
        token(self.run_id, 'run_id'); revision(self.revision)
        sha256(self.candidate_digest, 'candidate_digest')
        for field, cls, key, minimum in (
            ('sources', Source, 'source_id', 1), ('blocks', Block, 'block_id', 1),
            ('outputs', Output, 'output_id', 1), ('citations', Citation, 'citation_id', 0),
            ('claims', Claim, 'claim_id', 1)):
            records(getattr(self, field), cls, field, key, minimum)
        refs = [s.artifact for s in self.sources] + [o.artifact for o in self.outputs]
        if len({a.artifact_id for a in refs}) != len(refs) or len({a.path for a in refs}) != len(refs):
            raise ContractError('DUPLICATE_ARTIFACT_ID_OR_PATH')
        if sum(a.size for a in refs) > MAX_TOTAL_BYTES:
            raise ContractError('TOTAL_SOURCE_IO_LIMIT')
        if sum(len(b.text) for b in self.blocks) + sum(len(c.text) for c in self.claims) + sum(len(c.quote) for c in self.citations) > 8 * MAX_TEXT:
            raise ContractError('TOTAL_BLOCK_TEXT_LIMIT')
        # Duplicate source spans must not masquerade as independent evidence.
        positions = [(c.block_id, c.start, c.end) for c in self.citations]
        if len(set(positions)) != len(positions):
            raise ContractError('DUPLICATE_CITATION_SPAN')
        positions = [(c.output_id, c.start, c.end) for c in self.claims]
        if len(set(positions)) != len(positions):
            raise ContractError('DUPLICATE_CLAIM_SPAN')

    def to_dict(self) -> dict:
        # Declaration order is intentionally part of identity; changing it
        # invalidates attestations rather than silently reusing their support.
        return asdict(self)

    @property
    def content_digest(self) -> str:
        return digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class Policy:
    """Operator-owned scope; never load this from a submitted request/receipt."""
    policy_id: str
    expected_output_ids: tuple[str, ...]
    minimum_confidence_ppm: int = 900_000
    minimum_extraction_confidence_ppm: int = 900_000
    max_receipt_age_seconds: int = 604800

    def __post_init__(self):
        token(self.policy_id, 'policy_id')
        tuple_tokens(self.expected_output_ids, 'expected_output_ids', 1, MAX_ITEMS)
        integer(self.minimum_confidence_ppm, 'minimum_confidence_ppm', 900_000, 1_000_000)
        integer(self.minimum_extraction_confidence_ppm, 'minimum_extraction_confidence_ppm', 900_000, 1_000_000)
        integer(self.max_receipt_age_seconds, 'max_receipt_age_seconds', 1, 604800)

    @property
    def content_digest(self):
        return digest(asdict(self))


@dataclass(frozen=True, slots=True)
class Finding:
    code: str
    severity: str
    subject_id: str
    owner: str
    detail: str

    def __post_init__(self):
        for field in ('code', 'subject_id', 'owner'):
            token(getattr(self, field), field)
        choice(self.severity, ('BLOCKER', 'REVIEW', 'INFO'), 'severity')
        text(self.detail, 'detail', 4096)


@dataclass(frozen=True, slots=True)
class Report:
    task_id: str
    request_digest: str
    policy_digest: str
    evidence_digest: str
    evaluated_at: int
    findings: tuple[Finding, ...]
    measurements: tuple[tuple[str, int], ...]
    inspected_artifact_ids: tuple[str, ...]
    limitations: tuple[str, ...]

    @property
    def status(self):
        if any(f.severity == 'BLOCKER' for f in self.findings): return 'BLOCKED'
        if any(f.severity == 'REVIEW' for f in self.findings): return 'REVIEW_REQUIRED'
        return 'CHECKS_PASSED'

    @property
    def product_accepted(self): return False

    def to_dict(self):
        data = asdict(self)
        data.update(status=self.status, product_accepted=False)
        return data

    @property
    def content_digest(self): return digest(self.to_dict())
