from dataclasses import dataclass, field, asdict
from typing import Any

@dataclass
class Source:
    page: int
    chapter: str | None = None
    section: str | None = None
    block_id: str | None = None
    char_start: int | None = None
    char_end: int | None = None

@dataclass
class InformationUnit:
    id: str
    type: list[str]
    content: dict[str, Any]
    source: Source
    confidence: float = 1.0
    questions: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    relations: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    applications: list[dict[str, Any]] = field(default_factory=list)
    validation: dict[str, Any] = field(default_factory=dict)

@dataclass
class Relationship:
    source: str
    relation: str
    target: str
    confidence: float = 1.0
    evidence: list[Source] = field(default_factory=list)

@dataclass
class Book:
    book_id: str
    metadata: dict[str, Any]
    structure: dict[str, Any]
    information_units: list[InformationUnit] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    figures: list[dict[str, Any]] = field(default_factory=list)
    tables: list[dict[str, Any]] = field(default_factory=list)
    equations: list[dict[str, Any]] = field(default_factory=list)
    validation: dict[str, Any] = field(default_factory=dict)


def to_dict(obj):
    return asdict(obj)
