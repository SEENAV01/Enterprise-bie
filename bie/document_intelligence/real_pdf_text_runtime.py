"""Source-linked native PDF text runtime composed from canonical DI contracts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .layout_segmentation import LayoutError, Region, normalize as normalize_regions
from .page_mapping import Anchor as PageMapAnchor
from .page_mapping import PageMapError, validate as validate_page_map
from .pdfplumber_text_adapter import (
    NativeTextDocument,
    NativeTextLine,
    PdfPlumberTextAdapter,
    PdfPlumberTextAdapterError,
)
from .reading_order import ReadingOrderError, edges, validate_order
from .real_pdf_runtime import RealPdfRuntimeError, inspect_real_pdf
from .source_anchors import Anchor as SourceAnchor
from .source_anchors import E as SourceAnchorError
from .source_anchors import validate as validate_source_anchor
from .text_blocks import TextBlock, TextBlockError, build as build_text_block


READING_ORDER_POLICY = "top_then_left_v1"
# This confidence records direct native-PDF extraction observation only. It is
# not an OCR, semantic, factual, or reading-order correctness confidence.
DIRECT_NATIVE_PDF_EXTRACTION_CONFIDENCE = 1.0


class RealPdfTextRuntimeError(ValueError):
    """Raised when source-linked native PDF text cannot be validated safely."""


@dataclass(frozen=True)
class SourceLinkedTextBlock:
    block: TextBlock
    region: Region
    source_anchor: SourceAnchor
    page_map_anchor: PageMapAnchor
    order_index: int

    def to_safe_dict(self) -> dict[str, object]:
        text_bytes = self.block.text.encode("utf-8")
        return {
            "block_id": self.block.block_id,
            "region_id": self.region.region_id,
            "page": self.block.page,
            "order_index": self.order_index,
            "box": list(self.region.box),
            "char_count": len(self.block.text),
            "text_sha256": hashlib.sha256(text_bytes).hexdigest(),
        }


@dataclass(frozen=True)
class PageTextLayout:
    page: int
    ordered_region_ids: tuple[str, ...]
    reading_order_edges: tuple[tuple[str, str], ...]
    source_linked_blocks: tuple[SourceLinkedTextBlock, ...]

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "page": self.page,
            "block_count": len(self.source_linked_blocks),
            "ordered_region_ids": list(self.ordered_region_ids),
            "reading_order_edges": [list(edge) for edge in self.reading_order_edges],
            "blocks": [item.to_safe_dict() for item in self.source_linked_blocks],
        }


@dataclass(frozen=True)
class RealPdfTextInspection:
    source_hash: str
    byte_length: int
    page_count: int
    text_pages: int
    total_blocks: int
    reading_order_policy: str
    pages: tuple[PageTextLayout, ...]

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "source_hash": self.source_hash,
            "byte_length": self.byte_length,
            "page_count": self.page_count,
            "text_pages": self.text_pages,
            "total_blocks": self.total_blocks,
            "reading_order_policy": self.reading_order_policy,
            "pages": [page.to_safe_dict() for page in self.pages],
        }


def _line_sort_key(item: tuple[int, NativeTextLine]) -> tuple[object, ...]:
    extraction_index, line = item
    return (
        line.top,
        line.x0,
        line.bottom,
        line.x1,
        line.text,
        extraction_index,
    )


def _validate_linked_item(
    item: SourceLinkedTextBlock,
    *,
    page: int,
    source_hash: str,
) -> None:
    region_id = item.region.region_id
    if item.block.page != page:
        raise RealPdfTextRuntimeError("text block page mismatch")
    if item.block.region_ids != (region_id,):
        raise RealPdfTextRuntimeError("text block region mismatch")
    if item.source_anchor.page != page or item.source_anchor.region_id != region_id:
        raise RealPdfTextRuntimeError("source anchor linkage mismatch")
    if item.page_map_anchor.physical_page != page:
        raise RealPdfTextRuntimeError("page-map page mismatch")
    if item.page_map_anchor.logical_id != item.block.block_id:
        raise RealPdfTextRuntimeError("page-map logical ID mismatch")
    if item.page_map_anchor.region_id != region_id:
        raise RealPdfTextRuntimeError("page-map region mismatch")
    if not (
        item.region.box
        == item.source_anchor.box
        == item.page_map_anchor.box
    ):
        raise RealPdfTextRuntimeError("linked geometry mismatch")
    if item.source_anchor.source_hash != source_hash:
        raise RealPdfTextRuntimeError("source anchor hash mismatch")


def _build_page(
    lines: tuple[NativeTextLine, ...],
    *,
    page: int,
    source_hash: str,
) -> tuple[PageTextLayout, tuple[PageMapAnchor, ...]]:
    if any(line.page != page for line in lines):
        raise RealPdfTextRuntimeError("native text line page mismatch")
    ordered_lines = [line for _, line in sorted(enumerate(lines), key=_line_sort_key)]
    regions = tuple(
        Region(
            region_id=f"p{page:04d}-r{position:04d}",
            kind="text",
            box=line.box,
            confidence=DIRECT_NATIVE_PDF_EXTRACTION_CONFIDENCE,
        )
        for position, line in enumerate(ordered_lines, start=1)
    )
    normalized_regions = normalize_regions(regions)
    region_ids = tuple(region.region_id for region in normalized_regions)
    ordered_region_ids = validate_order(region_ids, region_ids)
    region_edges = edges(ordered_region_ids)

    linked: list[SourceLinkedTextBlock] = []
    page_map_anchors: list[PageMapAnchor] = []
    for order_index, (line, region) in enumerate(
        zip(ordered_lines, normalized_regions, strict=True)
    ):
        block = build_text_block(
            f"p{page:04d}-b{order_index + 1:04d}",
            line.text,
            (region.region_id,),
            page,
            DIRECT_NATIVE_PDF_EXTRACTION_CONFIDENCE,
        )
        source_anchor = SourceAnchor(
            source_hash=source_hash,
            page=page,
            region_id=region.region_id,
            box=region.box,
        )
        validate_source_anchor(source_anchor)
        page_map_anchor = PageMapAnchor(
            logical_id=block.block_id,
            physical_page=page,
            region_id=region.region_id,
            box=region.box,
        )
        item = SourceLinkedTextBlock(
            block=block,
            region=region,
            source_anchor=source_anchor,
            page_map_anchor=page_map_anchor,
            order_index=order_index,
        )
        _validate_linked_item(item, page=page, source_hash=source_hash)
        linked.append(item)
        page_map_anchors.append(page_map_anchor)

    if len({item.region.region_id for item in linked}) != len(linked):
        raise RealPdfTextRuntimeError("regions must have exactly one source anchor")
    if len({item.block.block_id for item in linked}) != len(linked):
        raise RealPdfTextRuntimeError("blocks must have exactly one page-map anchor")

    return (
        PageTextLayout(
            page=page,
            ordered_region_ids=ordered_region_ids,
            reading_order_edges=region_edges,
            source_linked_blocks=tuple(linked),
        ),
        tuple(page_map_anchors),
    )


def inspect_real_pdf_text(
    data: bytes | bytearray,
    *,
    text_adapter: PdfPlumberTextAdapter | None = None,
) -> RealPdfTextInspection:
    """Inspect native PDF text through canonical layout/provenance contracts."""

    if not isinstance(data, (bytes, bytearray)):
        raise RealPdfTextRuntimeError("PDF input must be bytes")
    payload = bytes(data)

    try:
        base = inspect_real_pdf(payload)
        extracted: NativeTextDocument = (text_adapter or PdfPlumberTextAdapter()).extract(
            payload
        )
        if extracted.page_count != base.page_count:
            raise RealPdfTextRuntimeError("pypdf/pdfplumber page-count mismatch")
        if tuple(page.page for page in extracted.pages) != tuple(
            range(1, base.page_count + 1)
        ):
            raise RealPdfTextRuntimeError("pdfplumber page sequence mismatch")

        pages: list[PageTextLayout] = []
        page_map_anchors: list[PageMapAnchor] = []
        for extracted_page in extracted.pages:
            page, anchors = _build_page(
                extracted_page.lines,
                page=extracted_page.page,
                source_hash=base.source_hash,
            )
            pages.append(page)
            page_map_anchors.extend(anchors)
        validate_page_map(page_map_anchors, base.page_count)
    except RealPdfTextRuntimeError:
        raise
    except (
        LayoutError,
        PageMapError,
        PdfPlumberTextAdapterError,
        ReadingOrderError,
        RealPdfRuntimeError,
        SourceAnchorError,
        TextBlockError,
    ) as exc:
        raise RealPdfTextRuntimeError("real PDF text inspection failed") from exc

    page_results = tuple(pages)
    return RealPdfTextInspection(
        source_hash=base.source_hash,
        byte_length=base.byte_length,
        page_count=base.page_count,
        text_pages=base.text_pages,
        total_blocks=sum(len(page.source_linked_blocks) for page in page_results),
        reading_order_policy=READING_ORDER_POLICY,
        pages=page_results,
    )
