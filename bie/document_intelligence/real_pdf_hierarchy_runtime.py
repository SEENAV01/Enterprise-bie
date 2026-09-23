"""Deterministic hierarchy candidates over verified native-PDF structure signals."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, replace
import hashlib
import re

from . import chapter_structure, section_structure, source_anchors, subsection_structure
from .real_pdf_structure_runtime import (
    BlockStructureSignal,
    RealPdfStructureRuntimeError,
    inspect_real_pdf_structure,
)
from .source_anchors import Anchor


HIERARCHY_POLICY = "numbered_heading_hierarchy_v1"


class RealPdfHierarchyRuntimeError(ValueError):
    """Raised when hierarchy candidates cannot be aligned or validated safely."""


@dataclass(frozen=True)
class HierarchyCandidate:
    candidate_id: str
    block_id: str
    region_id: str
    page: int
    source_anchor: Anchor
    heading_score: float
    numbering: tuple[int, ...] | None
    proposed_level: str
    global_order: int
    structure_order_position: int
    text: str
    resolution_status: str
    reason_code: str | None

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "block_id": self.block_id,
            "region_id": self.region_id,
            "page": self.page,
            "source_anchor": {
                "source_hash": self.source_anchor.source_hash,
                "page": self.source_anchor.page,
                "region_id": self.source_anchor.region_id,
                "box": list(self.source_anchor.box),
            },
            "text_sha256": hashlib.sha256(self.text.encode("utf-8")).hexdigest(),
            "char_count": len(self.text),
            "heading_score": self.heading_score,
            "numbering_components": (
                list(self.numbering) if self.numbering is not None else None
            ),
            "proposed_level": self.proposed_level,
            "resolution_status": self.resolution_status,
            "reason_code": self.reason_code,
            "global_order": self.global_order,
            "structure_order_position": self.structure_order_position,
        }


@dataclass(frozen=True)
class MaterializedChapter:
    candidate_id: str
    numbering: tuple[int, ...]
    chapter: chapter_structure.Chapter
    source_anchor: Anchor

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "numbering_components": list(self.numbering),
            "chapter_id": self.chapter.chapter_id,
            "start_page": self.chapter.start_page,
            "end_page": self.chapter.end_page,
            "order": self.chapter.order,
            "source_anchor_region_id": self.source_anchor.region_id,
        }


@dataclass(frozen=True)
class MaterializedSection:
    candidate_id: str
    numbering: tuple[int, ...]
    section: section_structure.Section
    source_anchor: Anchor

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "numbering_components": list(self.numbering),
            "section_id": self.section.section_id,
            "chapter_id": self.section.chapter_id,
            "order": self.section.order,
            "source_anchor": self.section.source_anchor,
            "source_anchor_region_id": self.source_anchor.region_id,
        }


@dataclass(frozen=True)
class MaterializedSubsection:
    candidate_id: str
    numbering: tuple[int, ...]
    subsection_id: str
    section_id: str
    order: int
    source_anchor: Anchor
    title: str

    def canonical_node(self) -> dict[str, object]:
        return {
            "id": self.subsection_id,
            "section_id": self.section_id,
            "title": self.title,
            "order": self.order,
        }

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "numbering_components": list(self.numbering),
            "subsection_id": self.subsection_id,
            "section_id": self.section_id,
            "order": self.order,
            "source_anchor_region_id": self.source_anchor.region_id,
        }


@dataclass(frozen=True)
class RealPdfHierarchyInspection:
    source_hash: str
    byte_length: int
    page_count: int
    total_blocks: int
    heading_candidate_count: int
    hierarchy_policy: str
    candidate_count: int
    chapter_candidate_count: int
    section_candidate_count: int
    subsection_candidate_count: int
    unresolved_candidate_count: int
    materialized_chapter_count: int
    materialized_section_count: int
    materialized_subsection_count: int
    candidates: tuple[HierarchyCandidate, ...]
    chapters: tuple[MaterializedChapter, ...]
    sections: tuple[MaterializedSection, ...]
    subsections: tuple[MaterializedSubsection, ...]

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "source_hash": self.source_hash,
            "byte_length": self.byte_length,
            "page_count": self.page_count,
            "total_blocks": self.total_blocks,
            "heading_candidate_count": self.heading_candidate_count,
            "hierarchy_policy": self.hierarchy_policy,
            "candidate_count": self.candidate_count,
            "chapter_candidate_count": self.chapter_candidate_count,
            "section_candidate_count": self.section_candidate_count,
            "subsection_candidate_count": self.subsection_candidate_count,
            "unresolved_candidate_count": self.unresolved_candidate_count,
            "materialized_chapter_count": self.materialized_chapter_count,
            "materialized_section_count": self.materialized_section_count,
            "materialized_subsection_count": self.materialized_subsection_count,
            "candidates": [candidate.to_safe_dict() for candidate in self.candidates],
            "chapters": [chapter.to_safe_dict() for chapter in self.chapters],
            "sections": [section.to_safe_dict() for section in self.sections],
            "subsections": [subsection.to_safe_dict() for subsection in self.subsections],
        }


_CHAPTER_PATTERN = re.compile(
    r"^CHAPTER\s+([1-9]\d*)(?:(?:\s*[:.-])?\s+.+)?$", re.IGNORECASE
)
_NUMBERED_PATTERN = re.compile(
    r"^([1-9]\d*(?:\.[1-9]\d*)*)(?:\.)?(?:\s+.+)?$"
)
_UNSUPPORTED_PREFIX = re.compile(
    r"^(?:CHAPTER\s+)?(?:[IVXLCDM]+|[A-Z])(?:[.)]|\s)", re.IGNORECASE
)
_NUMERIC_LIKE_PREFIX = re.compile(r"^\d")


def _classify(text: str) -> tuple[tuple[int, ...] | None, str, str | None]:
    stripped = text.strip()
    chapter = _CHAPTER_PATTERN.fullmatch(stripped)
    if chapter:
        return (int(chapter.group(1)),), "chapter", None

    numbered = _NUMBERED_PATTERN.fullmatch(stripped)
    if numbered:
        components = tuple(int(value) for value in numbered.group(1).split("."))
        if not components or any(value < 1 for value in components):
            return None, "unresolved", "unsupported_numbering"
        if len(components) == 1:
            return components, "chapter", None
        if len(components) == 2:
            return components, "section", None
        return components, "subsection", None

    if _UNSUPPORTED_PREFIX.match(stripped) or _NUMERIC_LIKE_PREFIX.match(stripped):
        return None, "unresolved", "unsupported_numbering"
    return None, "unresolved", "unnumbered_heading"


def _candidate_id(level: str, region_id: str) -> str:
    prefix = {
        "chapter": "ch",
        "section": "sec",
        "subsection": "sub",
        "unresolved": "cand",
    }[level]
    return f"{prefix}-{region_id}"


def _collect_candidates(structure_result) -> tuple[HierarchyCandidate, ...]:
    candidates: list[HierarchyCandidate] = []
    seen_candidate_regions: set[str] = set()
    for page in sorted(structure_result.pages, key=lambda item: item.page):
        by_region: dict[str, BlockStructureSignal] = {}
        for signal in page.blocks:
            if signal.region_id in by_region:
                raise RealPdfHierarchyRuntimeError("duplicate region in structure page")
            by_region[signal.region_id] = signal
        if len(page.structure_order) != len(set(page.structure_order)):
            raise RealPdfHierarchyRuntimeError("duplicate region in structure order")
        if set(page.structure_order) != set(by_region):
            raise RealPdfHierarchyRuntimeError("structure order is not an exact permutation")

        ordered_candidate_regions: list[str] = []
        for position, region_id in enumerate(page.structure_order, start=1):
            signal = by_region[region_id]
            if not signal.heading_candidate:
                continue
            if region_id in seen_candidate_regions:
                raise RealPdfHierarchyRuntimeError("heading candidate region is not unique")
            seen_candidate_regions.add(region_id)
            ordered_candidate_regions.append(region_id)
            text = signal.source_linked_block.block.text
            numbering, level, reason = _classify(text)
            anchor = signal.source_linked_block.source_anchor
            if (
                anchor.source_hash != structure_result.source_hash
                or anchor.page != page.page
                or anchor.region_id != region_id
                or anchor.box != signal.source_linked_block.region.box
            ):
                raise RealPdfHierarchyRuntimeError("candidate source anchor mismatch")
            source_anchors.validate(anchor)
            candidates.append(
                HierarchyCandidate(
                    candidate_id=_candidate_id(level, region_id),
                    block_id=signal.block_id,
                    region_id=region_id,
                    page=page.page,
                    source_anchor=anchor,
                    heading_score=signal.heading_score,
                    numbering=numbering,
                    proposed_level=level,
                    global_order=len(candidates) + 1,
                    structure_order_position=position,
                    text=text,
                    resolution_status="unresolved" if reason else "candidate",
                    reason_code=reason,
                )
            )
        if len(page.heading_candidate_region_ids) != len(
            set(page.heading_candidate_region_ids)
        ) or set(ordered_candidate_regions) != set(page.heading_candidate_region_ids):
            raise RealPdfHierarchyRuntimeError("heading candidate coverage mismatch")
    if len(candidates) != structure_result.heading_candidate_count:
        raise RealPdfHierarchyRuntimeError("heading candidate count mismatch")
    return tuple(candidates)


def _mark_duplicate_numbering(
    candidates: tuple[HierarchyCandidate, ...],
) -> tuple[HierarchyCandidate, ...]:
    counts = Counter(
        candidate.numbering
        for candidate in candidates
        if candidate.numbering is not None and candidate.reason_code is None
    )
    return tuple(
        replace(
            candidate,
            resolution_status="unresolved",
            reason_code="duplicate_numbering",
        )
        if candidate.numbering is not None and counts[candidate.numbering] > 1
        else candidate
        for candidate in candidates
    )


def _materialize(
    candidates: tuple[HierarchyCandidate, ...],
    *,
    page_count: int,
) -> tuple[
    tuple[HierarchyCandidate, ...],
    tuple[MaterializedChapter, ...],
    tuple[MaterializedSection, ...],
    tuple[MaterializedSubsection, ...],
]:
    working = list(_mark_duplicate_numbering(candidates))
    chapter_indexes = [
        index
        for index, candidate in enumerate(working)
        if candidate.proposed_level == "chapter" and candidate.reason_code is None
    ]
    chapters_by_page: dict[int, list[int]] = defaultdict(list)
    for index in chapter_indexes:
        chapters_by_page[working[index].page].append(index)
    ambiguous_indexes = {
        index
        for indexes in chapters_by_page.values()
        if len(indexes) > 1
        for index in indexes
    }
    for index in sorted(ambiguous_indexes):
        working[index] = replace(
            working[index],
            resolution_status="unresolved",
            reason_code="ambiguous_chapter_boundary",
        )

    chapter_indexes = [
        index
        for index, candidate in enumerate(working)
        if candidate.proposed_level == "chapter" and candidate.reason_code is None
    ]
    materialized_chapters: list[MaterializedChapter] = []
    for order, index in enumerate(chapter_indexes, start=1):
        candidate = working[index]
        next_page = (
            working[chapter_indexes[order]].page
            if order < len(chapter_indexes)
            else page_count + 1
        )
        chapter = chapter_structure.Chapter(
            chapter_id=candidate.candidate_id,
            title=candidate.text,
            start_page=candidate.page,
            end_page=next_page - 1,
            order=order,
        )
        materialized_chapters.append(
            MaterializedChapter(
                candidate_id=candidate.candidate_id,
                numbering=candidate.numbering or (),
                chapter=chapter,
                source_anchor=candidate.source_anchor,
            )
        )
        working[index] = replace(candidate, resolution_status="materialized")
    chapter_structure.validate(tuple(item.chapter for item in materialized_chapters))
    chapter_by_number = {item.numbering: item for item in materialized_chapters}

    section_orders: dict[str, int] = defaultdict(int)
    materialized_sections: list[MaterializedSection] = []
    for index, candidate in enumerate(working):
        if candidate.proposed_level != "section" or candidate.reason_code is not None:
            continue
        parent = chapter_by_number.get((candidate.numbering or ())[0:1])
        if parent is None:
            working[index] = replace(
                candidate,
                resolution_status="unresolved",
                reason_code="missing_chapter_parent",
            )
            continue
        section_orders[parent.chapter.chapter_id] += 1
        section = section_structure.Section(
            section_id=candidate.candidate_id,
            chapter_id=parent.chapter.chapter_id,
            title=candidate.text,
            order=section_orders[parent.chapter.chapter_id],
            source_anchor=f"p{candidate.page}:{candidate.region_id}",
        )
        materialized_sections.append(
            MaterializedSection(
                candidate_id=candidate.candidate_id,
                numbering=candidate.numbering or (),
                section=section,
                source_anchor=candidate.source_anchor,
            )
        )
        working[index] = replace(candidate, resolution_status="materialized")
    section_structure.validate(tuple(item.section for item in materialized_sections))
    section_by_number = {item.numbering: item for item in materialized_sections}

    subsection_orders: dict[str, int] = defaultdict(int)
    materialized_subsections: list[MaterializedSubsection] = []
    for index, candidate in enumerate(working):
        if candidate.proposed_level != "subsection" or candidate.reason_code is not None:
            continue
        parent = section_by_number.get((candidate.numbering or ())[:2])
        if parent is None:
            working[index] = replace(
                candidate,
                resolution_status="unresolved",
                reason_code="missing_section_parent",
            )
            continue
        subsection_orders[parent.section.section_id] += 1
        materialized_subsections.append(
            MaterializedSubsection(
                candidate_id=candidate.candidate_id,
                numbering=candidate.numbering or (),
                subsection_id=candidate.candidate_id,
                section_id=parent.section.section_id,
                order=subsection_orders[parent.section.section_id],
                source_anchor=candidate.source_anchor,
                title=candidate.text,
            )
        )
        working[index] = replace(candidate, resolution_status="materialized")
    subsection_structure.validate(
        tuple(item.canonical_node() for item in materialized_subsections),
        {item.section.section_id for item in materialized_sections},
    )

    return (
        tuple(working),
        tuple(materialized_chapters),
        tuple(materialized_sections),
        tuple(materialized_subsections),
    )


def inspect_real_pdf_hierarchy(
    data: bytes | bytearray,
) -> RealPdfHierarchyInspection:
    """Inspect conservative source-linked hierarchy candidates over Task 012."""

    if not isinstance(data, (bytes, bytearray)):
        raise RealPdfHierarchyRuntimeError("PDF input must be bytes")
    try:
        structure_result = inspect_real_pdf_structure(bytes(data))
        initial_candidates = _collect_candidates(structure_result)
        candidates, chapters, sections, subsections = _materialize(
            initial_candidates,
            page_count=structure_result.page_count,
        )
    except RealPdfHierarchyRuntimeError:
        raise
    except (
        chapter_structure.ChapterError,
        section_structure.SectionError,
        source_anchors.E,
        subsection_structure.SubsectionError,
        RealPdfStructureRuntimeError,
    ) as exc:
        raise RealPdfHierarchyRuntimeError(
            "real PDF hierarchy inspection failed"
        ) from exc

    unresolved_count = sum(
        candidate.resolution_status == "unresolved" for candidate in candidates
    )
    return RealPdfHierarchyInspection(
        source_hash=structure_result.source_hash,
        byte_length=structure_result.byte_length,
        page_count=structure_result.page_count,
        total_blocks=structure_result.total_blocks,
        heading_candidate_count=structure_result.heading_candidate_count,
        hierarchy_policy=HIERARCHY_POLICY,
        candidate_count=len(candidates),
        chapter_candidate_count=sum(
            candidate.proposed_level == "chapter" for candidate in candidates
        ),
        section_candidate_count=sum(
            candidate.proposed_level == "section" for candidate in candidates
        ),
        subsection_candidate_count=sum(
            candidate.proposed_level == "subsection" for candidate in candidates
        ),
        unresolved_candidate_count=unresolved_count,
        materialized_chapter_count=len(chapters),
        materialized_section_count=len(sections),
        materialized_subsection_count=len(subsections),
        candidates=candidates,
        chapters=chapters,
        sections=sections,
        subsections=subsections,
    )
