"""Native PDF outline reconciliation over verified hierarchy candidates."""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import dataclass
import hashlib

from . import toc_reconciliation
from .pypdf_outline_adapter import (
    NativeOutlineEntry,
    PyPdfOutlineAdapter,
    PyPdfOutlineAdapterError,
)
from .real_pdf_hierarchy_runtime import (
    RealPdfHierarchyRuntimeError,
    inspect_real_pdf_hierarchy,
)


TOC_RECONCILIATION_POLICY = "native_outline_exact_title_v1"


class RealPdfTocRuntimeError(ValueError):
    """Raised when native outline reconciliation cannot be validated safely."""


@dataclass(frozen=True)
class _DetectedHierarchyNode:
    detected_id: str
    title: str
    level: str
    page: int


def _title_hash(title: str) -> str:
    return hashlib.sha256(title.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TocReconciliationMatch:
    outline_order: int
    depth: int
    outline_page: int
    title_sha256: str
    char_count: int
    detected_id: str
    detected_level: str
    detected_page: int
    exact_page_match: bool
    page_delta: int

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "outline_order": self.outline_order,
            "depth": self.depth,
            "outline_page": self.outline_page,
            "title_sha256": self.title_sha256,
            "char_count": self.char_count,
            "detected_id": self.detected_id,
            "detected_level": self.detected_level,
            "detected_page": self.detected_page,
            "exact_page_match": self.exact_page_match,
            "page_delta": self.page_delta,
        }


@dataclass(frozen=True)
class TocReconciliationUnmatched:
    outline_order: int
    depth: int
    destination_page: int | None
    title_sha256: str
    char_count: int
    reason_code: str

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "outline_order": self.outline_order,
            "depth": self.depth,
            "destination_page": self.destination_page,
            "title_sha256": self.title_sha256,
            "char_count": self.char_count,
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class RealPdfTocInspection:
    source_hash: str
    byte_length: int
    page_count: int
    total_blocks: int
    hierarchy_policy: str
    toc_reconciliation_policy: str
    heading_candidate_count: int
    materialized_chapter_count: int
    materialized_section_count: int
    materialized_subsection_count: int
    native_outline_entry_count: int
    outline_depth_distribution: tuple[tuple[int, int], ...]
    outline_resolvable_page_count: int
    reconciliation_match_count: int
    unmatched_outline_count: int
    ambiguous_detected_title_count: int
    exact_page_match_count: int
    page_delta_distribution: tuple[tuple[int, int], ...]
    outline_status: str
    matches: tuple[TocReconciliationMatch, ...]
    unmatched_outline_entries: tuple[TocReconciliationUnmatched, ...]

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "source_hash": self.source_hash,
            "byte_length": self.byte_length,
            "page_count": self.page_count,
            "total_blocks": self.total_blocks,
            "hierarchy_policy": self.hierarchy_policy,
            "toc_reconciliation_policy": self.toc_reconciliation_policy,
            "heading_candidate_count": self.heading_candidate_count,
            "materialized_chapter_count": self.materialized_chapter_count,
            "materialized_section_count": self.materialized_section_count,
            "materialized_subsection_count": self.materialized_subsection_count,
            "native_outline_entry_count": self.native_outline_entry_count,
            "outline_depth_distribution": {
                str(depth): count for depth, count in self.outline_depth_distribution
            },
            "outline_resolvable_page_count": self.outline_resolvable_page_count,
            "reconciliation_match_count": self.reconciliation_match_count,
            "unmatched_outline_count": self.unmatched_outline_count,
            "ambiguous_detected_title_count": self.ambiguous_detected_title_count,
            "exact_page_match_count": self.exact_page_match_count,
            "page_delta_distribution": {
                str(delta): count for delta, count in self.page_delta_distribution
            },
            "outline_status": self.outline_status,
            "matches": [match.to_safe_dict() for match in self.matches],
            "unmatched_outline_entries": [
                entry.to_safe_dict() for entry in self.unmatched_outline_entries
            ],
        }


def _normalize_title(title: str) -> str:
    normalized = title.strip().casefold()
    if not normalized:
        raise RealPdfTocRuntimeError("hierarchy title is empty")
    return normalized


def _detected_hierarchy_nodes(hierarchy) -> tuple[_DetectedHierarchyNode, ...]:
    nodes: list[_DetectedHierarchyNode] = []
    for item in hierarchy.chapters:
        nodes.append(
            _DetectedHierarchyNode(
                detected_id=item.chapter.chapter_id,
                title=item.chapter.title,
                level="chapter",
                page=item.chapter.start_page,
            )
        )
    for item in hierarchy.sections:
        nodes.append(
            _DetectedHierarchyNode(
                detected_id=item.section.section_id,
                title=item.section.title,
                level="section",
                page=item.source_anchor.page,
            )
        )
    for item in hierarchy.subsections:
        nodes.append(
            _DetectedHierarchyNode(
                detected_id=item.subsection_id,
                title=item.title,
                level="subsection",
                page=item.source_anchor.page,
            )
        )

    if len({node.detected_id for node in nodes}) != len(nodes):
        raise RealPdfTocRuntimeError("duplicate materialized hierarchy ID")
    for node in nodes:
        _normalize_title(node.title)
        if not 1 <= node.page <= hierarchy.page_count:
            raise RealPdfTocRuntimeError("hierarchy source page is outside the document")
    return tuple(nodes)


def _unmatched(entry: NativeOutlineEntry, reason: str) -> TocReconciliationUnmatched:
    return TocReconciliationUnmatched(
        outline_order=entry.order,
        depth=entry.depth,
        destination_page=entry.destination_page,
        title_sha256=_title_hash(entry.title),
        char_count=len(entry.title),
        reason_code=reason,
    )


def inspect_real_pdf_toc(data: bytes | bytearray) -> RealPdfTocInspection:
    """Reconcile native bookmarks with materialized Task 014 hierarchy nodes."""

    if not isinstance(data, (bytes, bytearray)):
        raise RealPdfTocRuntimeError("PDF input must be bytes")
    payload = bytes(data)

    try:
        hierarchy = inspect_real_pdf_hierarchy(payload)
        outline = PyPdfOutlineAdapter().inspect(payload)
    except (RealPdfHierarchyRuntimeError, PyPdfOutlineAdapterError) as exc:
        raise RealPdfTocRuntimeError("real PDF TOC inspection failed") from exc

    if outline.page_count != hierarchy.page_count:
        raise RealPdfTocRuntimeError("outline and hierarchy page counts disagree")
    if tuple(entry.order for entry in outline.entries) != tuple(
        range(1, len(outline.entries) + 1)
    ):
        raise RealPdfTocRuntimeError("native outline order is not deterministic")

    detected = _detected_hierarchy_nodes(hierarchy)
    normalized_counts = Counter(_normalize_title(node.title) for node in detected)
    ambiguous_titles = {
        title for title, count in normalized_counts.items() if count > 1
    }
    unambiguous_detected = tuple(
        node
        for node in detected
        if _normalize_title(node.title) not in ambiguous_titles
    )

    eligible: list[NativeOutlineEntry] = []
    unmatched: list[TocReconciliationUnmatched] = []
    for entry in outline.entries:
        normalized = _normalize_title(entry.title)
        if entry.destination_page is None:
            unmatched.append(_unmatched(entry, "outline_page_unresolved"))
        elif normalized in ambiguous_titles:
            unmatched.append(_unmatched(entry, "ambiguous_detected_title"))
        else:
            eligible.append(entry)

    try:
        canonical = toc_reconciliation.reconcile(
            [
                {"title": entry.title, "page": entry.destination_page}
                for entry in eligible
            ],
            [
                {"id": node.detected_id, "title": node.title}
                for node in unambiguous_detected
            ],
        )
    except toc_reconciliation.E as exc:
        raise RealPdfTocRuntimeError("canonical TOC reconciliation failed") from exc

    detected_by_id = {node.detected_id: node for node in unambiguous_detected}
    canonical_matches: dict[tuple[str, int | None], deque[dict[str, object]]] = (
        defaultdict(deque)
    )
    for match in canonical["matches"]:
        key = (_normalize_title(str(match["title"])), match.get("toc_page"))
        canonical_matches[key].append(match)

    matches: list[TocReconciliationMatch] = []
    for entry in eligible:
        key = (_normalize_title(entry.title), entry.destination_page)
        bucket = canonical_matches.get(key)
        if not bucket:
            unmatched.append(_unmatched(entry, "no_detected_title_match"))
            continue
        canonical_match = bucket.popleft()
        detected_id = canonical_match.get("detected_id")
        node = detected_by_id.get(str(detected_id))
        if node is None or entry.destination_page is None:
            raise RealPdfTocRuntimeError("canonical reconciliation returned invalid match")
        delta = entry.destination_page - node.page
        matches.append(
            TocReconciliationMatch(
                outline_order=entry.order,
                depth=entry.depth,
                outline_page=entry.destination_page,
                title_sha256=_title_hash(entry.title),
                char_count=len(entry.title),
                detected_id=node.detected_id,
                detected_level=node.level,
                detected_page=node.page,
                exact_page_match=delta == 0,
                page_delta=delta,
            )
        )

    if any(canonical_matches.values()):
        raise RealPdfTocRuntimeError("canonical reconciliation match coverage mismatch")
    if len(matches) + len(unmatched) != len(outline.entries):
        raise RealPdfTocRuntimeError("native outline reconciliation coverage mismatch")

    matches.sort(key=lambda item: item.outline_order)
    unmatched.sort(key=lambda item: item.outline_order)
    depth_counts = Counter(entry.depth for entry in outline.entries)
    delta_counts = Counter(match.page_delta for match in matches)

    return RealPdfTocInspection(
        source_hash=hierarchy.source_hash,
        byte_length=hierarchy.byte_length,
        page_count=hierarchy.page_count,
        total_blocks=hierarchy.total_blocks,
        hierarchy_policy=hierarchy.hierarchy_policy,
        toc_reconciliation_policy=TOC_RECONCILIATION_POLICY,
        heading_candidate_count=hierarchy.heading_candidate_count,
        materialized_chapter_count=hierarchy.materialized_chapter_count,
        materialized_section_count=hierarchy.materialized_section_count,
        materialized_subsection_count=hierarchy.materialized_subsection_count,
        native_outline_entry_count=len(outline.entries),
        outline_depth_distribution=tuple(sorted(depth_counts.items())),
        outline_resolvable_page_count=sum(
            entry.destination_page is not None for entry in outline.entries
        ),
        reconciliation_match_count=len(matches),
        unmatched_outline_count=len(unmatched),
        ambiguous_detected_title_count=len(ambiguous_titles),
        exact_page_match_count=sum(match.exact_page_match for match in matches),
        page_delta_distribution=tuple(sorted(delta_counts.items())),
        outline_status=(
            "no_native_outline" if not outline.entries else "native_outline_reconciled"
        ),
        matches=tuple(matches),
        unmatched_outline_entries=tuple(unmatched),
    )
