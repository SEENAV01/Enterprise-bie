"""Deterministic structure signals composed over source-linked native PDF text."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import re
from statistics import median

from . import block_provenance, heading_detection, multicolumn_layout
from .pdfplumber_structure_adapter import (
    NativeStructureDocument,
    NativeStructureLine,
    NativeStructurePage,
    PdfPlumberStructureAdapter,
    PdfPlumberStructureAdapterError,
)
from .reading_order import ReadingOrderError, edges, validate_order
from .real_pdf_text_runtime import (
    PageTextLayout,
    RealPdfTextRuntimeError,
    SourceLinkedTextBlock,
    inspect_real_pdf_text,
)


HEADING_FEATURE_POLICY = "heading_features_v1"
STRUCTURE_ORDER_POLICY = "structure_order_policy_v1"
PROVENANCE_METHOD = "native"


class RealPdfStructureRuntimeError(ValueError):
    """Raised when PDF structure signals cannot be aligned or validated safely."""


@dataclass(frozen=True)
class HeadingFeatures:
    font_scale: float
    bold: float
    spacing_before: float
    spacing_after: float
    shortness: float
    numbering: float

    def to_dict(self) -> dict[str, float]:
        return {
            "font_scale": self.font_scale,
            "bold": self.bold,
            "spacing_before": self.spacing_before,
            "spacing_after": self.spacing_after,
            "shortness": self.shortness,
            "numbering": self.numbering,
        }


@dataclass(frozen=True)
class BlockStructureSignal:
    source_linked_block: SourceLinkedTextBlock
    provenance_method: str
    heading_features: HeadingFeatures
    heading_score: float
    heading_candidate: bool
    column_index: int | None

    @property
    def block_id(self) -> str:
        return self.source_linked_block.block.block_id

    @property
    def region_id(self) -> str:
        return self.source_linked_block.region.region_id

    @property
    def page(self) -> int:
        return self.source_linked_block.block.page

    def to_safe_dict(self) -> dict[str, object]:
        item = self.source_linked_block
        text = item.block.text
        return {
            "block_id": item.block.block_id,
            "region_id": item.region.region_id,
            "page": item.block.page,
            "char_count": len(text),
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "box": list(item.region.box),
            "heading_features": self.heading_features.to_dict(),
            "heading_score": self.heading_score,
            "heading_candidate": self.heading_candidate,
            "column_index": self.column_index,
            "order_index": item.order_index,
            "provenance_method": self.provenance_method,
            "source_anchor_region_id": item.source_anchor.region_id,
        }


@dataclass(frozen=True)
class PageStructureSignals:
    page: int
    block_count: int
    heading_candidate_region_ids: tuple[str, ...]
    column_groups: tuple[tuple[str, ...], ...]
    column_count: int
    baseline_order: tuple[str, ...]
    structure_order: tuple[str, ...]
    structure_order_edges: tuple[tuple[str, str], ...]
    column_order_applied: bool
    fallback_reason: str | None
    blocks: tuple[BlockStructureSignal, ...]

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "page": self.page,
            "block_count": self.block_count,
            "heading_candidate_count": len(self.heading_candidate_region_ids),
            "heading_candidate_region_ids": list(
                self.heading_candidate_region_ids
            ),
            "column_count": self.column_count,
            "column_groups": [list(group) for group in self.column_groups],
            "baseline_order": list(self.baseline_order),
            "structure_order": list(self.structure_order),
            "structure_order_edges": [
                list(edge) for edge in self.structure_order_edges
            ],
            "column_order_applied": self.column_order_applied,
            "fallback_reason": self.fallback_reason,
            "blocks": [block.to_safe_dict() for block in self.blocks],
        }


@dataclass(frozen=True)
class RealPdfStructureInspection:
    source_hash: str
    byte_length: int
    page_count: int
    text_pages: int
    total_blocks: int
    heading_feature_policy: str
    structure_order_policy: str
    heading_candidate_count: int
    pages: tuple[PageStructureSignals, ...]

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "source_hash": self.source_hash,
            "byte_length": self.byte_length,
            "page_count": self.page_count,
            "text_pages": self.text_pages,
            "total_blocks": self.total_blocks,
            "heading_feature_policy": self.heading_feature_policy,
            "structure_order_policy": self.structure_order_policy,
            "heading_candidate_count": self.heading_candidate_count,
            "pages": [page.to_safe_dict() for page in self.pages],
        }


_NUMBERING_PATTERNS = (
    re.compile(r"^\d+$"),
    re.compile(r"^\d+\.(?:\s+|$)"),
    re.compile(r"^\d+(?:\.\d+){1,2}\.?(?:\s+|$)"),
    re.compile(r"^[IVXLCDM]+\.(?:\s+|$)", re.IGNORECASE),
    re.compile(r"^[A-Z]\.(?:\s+|$)"),
    re.compile(r"^CHAPTER\s+\d+(?:\s+|$)", re.IGNORECASE),
)


def _clamp(value: float) -> float:
    return round(min(1.0, max(0.0, value)), 8)


def _numbering_feature(text: str) -> float:
    return float(any(pattern.match(text) for pattern in _NUMBERING_PATTERNS))


def _align_page(
    text_page: PageTextLayout,
    structure_page: NativeStructurePage,
) -> tuple[tuple[SourceLinkedTextBlock, NativeStructureLine], ...]:
    if text_page.page != structure_page.page:
        raise RealPdfStructureRuntimeError("style/text page mismatch")
    linked = text_page.source_linked_blocks
    lines = structure_page.lines
    if len(linked) != len(lines):
        raise RealPdfStructureRuntimeError("style/text line count mismatch")

    aligned: list[tuple[SourceLinkedTextBlock, NativeStructureLine]] = []
    for item, line in zip(linked, lines, strict=True):
        if item.block.text.strip() != line.text:
            raise RealPdfStructureRuntimeError("style/text content mismatch")
        if item.block.page != line.page:
            raise RealPdfStructureRuntimeError("style/text page mismatch")
        if item.region.box != line.box:
            raise RealPdfStructureRuntimeError("style/text geometry mismatch")
        aligned.append((item, line))
    return tuple(aligned)


def _heading_features(
    lines: tuple[NativeStructureLine, ...],
) -> tuple[HeadingFeatures, ...]:
    if not lines:
        return ()
    body_font_size = float(median(line.representative_font_size for line in lines))
    line_height = float(median(line.bottom - line.top for line in lines))
    if body_font_size <= 0 or line_height <= 0:
        raise RealPdfStructureRuntimeError("invalid page typography reference")

    features: list[HeadingFeatures] = []
    for index, line in enumerate(lines):
        before = 0.0
        after = 0.0
        if index > 0:
            before = _clamp(max(0.0, line.top - lines[index - 1].bottom) / line_height)
        if index + 1 < len(lines):
            after = _clamp(max(0.0, lines[index + 1].top - line.bottom) / line_height)
        feature = HeadingFeatures(
            font_scale=_clamp(line.representative_font_size / body_font_size - 1.0),
            bold=_clamp(line.bold_fraction),
            spacing_before=before,
            spacing_after=after,
            shortness=_clamp(1.0 - line.char_count / 80.0),
            numbering=_numbering_feature(line.text),
        )
        if any(not 0.0 <= value <= 1.0 for value in feature.to_dict().values()):
            raise RealPdfStructureRuntimeError("heading feature is outside [0,1]")
        features.append(feature)
    return tuple(features)


def _column_result(
    signals: tuple[BlockStructureSignal, ...],
    lines: tuple[NativeStructureLine, ...],
    *,
    page_width: float,
    baseline_order: tuple[str, ...],
) -> tuple[
    tuple[tuple[str, ...], ...],
    tuple[str, ...],
    bool,
    str | None,
    dict[str, int],
]:
    if len(signals) != len(lines):
        raise RealPdfStructureRuntimeError("column input alignment mismatch")
    by_id = {
        signal.region_id: (signal, line)
        for signal, line in zip(signals, lines, strict=True)
    }
    regions = [
        {
            "id": signal.region_id,
            "kind": "heading" if signal.heading_candidate else "text",
            "box": (line.x0, line.top, line.x1, line.bottom),
        }
        for signal, line in zip(signals, lines, strict=True)
    ]
    groups = multicolumn_layout.detect_columns(regions, page_width)
    repeated = multicolumn_layout.detect_columns(regions, page_width)
    if groups != repeated:
        raise RealPdfStructureRuntimeError("column detection is not deterministic")

    flattened = tuple(region_id for group in groups for region_id in group)
    if len(flattened) != len(set(flattened)):
        raise RealPdfStructureRuntimeError("duplicate region in column groups")
    if any(region_id not in by_id for region_id in flattened):
        raise RealPdfStructureRuntimeError("unknown region in column groups")
    if set(flattened) != set(baseline_order):
        raise RealPdfStructureRuntimeError("column groups must cover every page region")

    if not baseline_order:
        return groups, baseline_order, False, "no_text_blocks", {}
    if len(groups) <= 1:
        column_map = {
            region_id: 0 for region_id in groups[0]
        } if groups else {}
        return groups, baseline_order, False, "single_column", column_map

    group_bounds = []
    for group in groups:
        left = min(by_id[region_id][1].x0 for region_id in group)
        right = max(by_id[region_id][1].x1 for region_id in group)
        group_bounds.append((left, right, group))
    ordered_groups = sorted(group_bounds, key=lambda item: (item[0], item[1], item[2]))
    if any(
        current[1] > following[0]
        for current, following in zip(ordered_groups, ordered_groups[1:])
    ):
        return groups, baseline_order, False, "ambiguous_column_overlap", {}

    structure_order: list[str] = []
    column_map: dict[str, int] = {}
    ordered_group_ids: list[tuple[str, ...]] = []
    for column_index, (_, _, group) in enumerate(ordered_groups):
        ordered = tuple(
            sorted(
                group,
                key=lambda region_id: (
                    by_id[region_id][1].top,
                    by_id[region_id][1].x0,
                    by_id[region_id][1].bottom,
                    by_id[region_id][1].x1,
                    by_id[region_id][0].source_linked_block.block.text,
                    region_id,
                ),
            )
        )
        ordered_group_ids.append(ordered)
        structure_order.extend(ordered)
        column_map.update({region_id: column_index for region_id in ordered})

    validated = validate_order(baseline_order, structure_order)
    return tuple(ordered_group_ids), validated, True, None, column_map


def _build_page(
    text_page: PageTextLayout,
    structure_page: NativeStructurePage,
) -> PageStructureSignals:
    aligned = _align_page(text_page, structure_page)
    lines = tuple(line for _, line in aligned)
    features = _heading_features(lines)
    signals: list[BlockStructureSignal] = []
    for (item, _), feature in zip(aligned, features, strict=True):
        feature_dict = feature.to_dict()
        score = heading_detection.heading_score(feature_dict)
        candidate = heading_detection.is_heading(feature_dict)
        if not block_provenance.validate(
            item.block.block_id,
            (item.region.region_id,),
            PROVENANCE_METHOD,
        ):
            raise RealPdfStructureRuntimeError("native block provenance rejected")
        signals.append(
            BlockStructureSignal(
                source_linked_block=item,
                provenance_method=PROVENANCE_METHOD,
                heading_features=feature,
                heading_score=score,
                heading_candidate=candidate,
                column_index=None,
            )
        )

    baseline_order = validate_order(
        tuple(signal.region_id for signal in signals),
        text_page.ordered_region_ids,
    )
    groups, structure_order, applied, reason, column_map = _column_result(
        tuple(signals),
        lines,
        page_width=structure_page.width,
        baseline_order=baseline_order,
    )
    final_signals = tuple(
        replace(signal, column_index=column_map.get(signal.region_id))
        for signal in signals
    )
    return PageStructureSignals(
        page=text_page.page,
        block_count=len(final_signals),
        heading_candidate_region_ids=tuple(
            signal.region_id for signal in final_signals if signal.heading_candidate
        ),
        column_groups=groups,
        column_count=len(groups),
        baseline_order=baseline_order,
        structure_order=structure_order,
        structure_order_edges=edges(structure_order),
        column_order_applied=applied,
        fallback_reason=reason,
        blocks=final_signals,
    )


def inspect_real_pdf_structure(
    data: bytes | bytearray,
    *,
    structure_adapter: PdfPlumberStructureAdapter | None = None,
) -> RealPdfStructureInspection:
    """Inspect deterministic native-PDF structure over Task 010 source links."""

    if not isinstance(data, (bytes, bytearray)):
        raise RealPdfStructureRuntimeError("PDF input must be bytes")
    payload = bytes(data)
    try:
        text_result = inspect_real_pdf_text(payload)
        structure: NativeStructureDocument = (
            structure_adapter or PdfPlumberStructureAdapter()
        ).extract(payload)
        if structure.page_count != text_result.page_count:
            raise RealPdfStructureRuntimeError("text/style page-count mismatch")
        if tuple(page.page for page in structure.pages) != tuple(
            range(1, text_result.page_count + 1)
        ):
            raise RealPdfStructureRuntimeError("style page sequence mismatch")

        pages = tuple(
            _build_page(text_page, structure_page)
            for text_page, structure_page in zip(
                text_result.pages, structure.pages, strict=True
            )
        )
    except RealPdfStructureRuntimeError:
        raise
    except (
        block_provenance.E,
        heading_detection.HeadingError,
        multicolumn_layout.ColumnError,
        PdfPlumberStructureAdapterError,
        ReadingOrderError,
        RealPdfTextRuntimeError,
    ) as exc:
        raise RealPdfStructureRuntimeError(
            "real PDF structure inspection failed"
        ) from exc

    return RealPdfStructureInspection(
        source_hash=text_result.source_hash,
        byte_length=text_result.byte_length,
        page_count=text_result.page_count,
        text_pages=text_result.text_pages,
        total_blocks=text_result.total_blocks,
        heading_feature_policy=HEADING_FEATURE_POLICY,
        structure_order_policy=STRUCTURE_ORDER_POLICY,
        heading_candidate_count=sum(
            len(page.heading_candidate_region_ids) for page in pages
        ),
        pages=pages,
    )
