"""Section16 SEM contracts. Submitted structure is not semantic truth.

Scopes and reference/concept inventories are operator policy. Numeric values use
bounded exact decimal strings; no floats, unit conversion, or silent coercion.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from fractions import Fraction
import re
from ..release_v2.contracts import ContractError, token, integer, sha256, choice, tuple_tokens, digest
from ..source_v2.models import Request as SourceRequest, Policy as SourcePolicy, records, text, MAX_ITEMS

VERSION = '1.0.0'
CHANNELS = ('narration', 'caption', 'on_screen', 'game_feedback', 'game_prompt', 'lesson')
_DECIMAL = re.compile(r'-?(?:0|[1-9][0-9]{0,11})(?:\.[0-9]{0,8}[1-9])?\Z', re.ASCII)


def number(value: str) -> Fraction:
    if type(value) is not str or not _DECIMAL.fullmatch(value) or value == '-0':
        raise ContractError('INVALID_EXACT_DECIMAL')
    return Fraction(value)


@dataclass(frozen=True, slots=True)
class Value:
    kind: str
    symbol: str = ''
    lower: str = ''
    upper: str = ''
    unit: str = ''

    def __post_init__(self):
        choice(self.kind, ('symbol', 'quantity'), 'value.kind')
        if self.kind == 'symbol':
            token(self.symbol, 'value.symbol')
            if (self.lower, self.upper, self.unit) != ('', '', ''):
                raise ContractError('SYMBOL_HAS_QUANTITY_FIELDS')
        else:
            if type(self.symbol) is not str or self.symbol != '':
                raise ContractError('QUANTITY_HAS_SYMBOL')
            token(self.unit, 'value.unit')
            if number(self.lower) > number(self.upper):
                raise ContractError('REVERSED_QUANTITY_RANGE')


@dataclass(frozen=True, slots=True)
class PredicateRule:
    predicate_id: str
    value_kind: str
    cardinality: str
    unit: str
    context_keys: tuple[str, ...]

    def __post_init__(self):
        token(self.predicate_id, 'predicate_id')
        choice(self.value_kind, ('symbol', 'quantity'), 'value_kind')
        choice(self.cardinality, ('single', 'multi'), 'cardinality')
        tuple_tokens(self.context_keys, 'context_keys', 1, 32)
        if self.context_keys != tuple(sorted(self.context_keys)):
            raise ContractError('NONCANONICAL_CONTEXT_KEYS')
        if self.value_kind == 'symbol':
            if type(self.unit) is not str or self.unit != '': raise ContractError('SYMBOL_RULE_UNIT')
        else:
            token(self.unit, 'rule.unit')
            if self.cardinality != 'single': raise ContractError('QUANTITY_MUST_BE_SINGLE')


@dataclass(frozen=True, slots=True)
class Proposition:
    entity_id: str
    predicate_id: str
    value: Value
    polarity: str
    context: tuple[tuple[str, str], ...]

    def __post_init__(self):
        token(self.entity_id, 'entity_id'); token(self.predicate_id, 'predicate_id')
        if type(self.value) is not Value: raise ContractError('INVALID_PROPOSITION_VALUE')
        choice(self.polarity, ('positive', 'negative'), 'polarity')
        if self.value.kind == 'quantity' and self.polarity != 'positive':
            raise ContractError('NEGATIVE_QUANTITY_UNSUPPORTED')
        if type(self.context) is not tuple or not 1 <= len(self.context) <= 32:
            raise ContractError('INVALID_CONTEXT')
        for row in self.context:
            if type(row) is not tuple or len(row) != 2: raise ContractError('INVALID_CONTEXT_PAIR')
            token(row[0], 'context.key'); token(row[1], 'context.value')
        if len({k for k, _ in self.context}) != len(self.context):
            raise ContractError('DUPLICATE_CONTEXT_KEY')
        if self.context != tuple(sorted(self.context)): raise ContractError('NONCANONICAL_CONTEXT')

    @property
    def content_digest(self): return digest(asdict(self))


@dataclass(frozen=True, slots=True)
class Normalization:
    claim_id: str
    propositions: tuple[Proposition, ...]

    def __post_init__(self):
        token(self.claim_id, 'claim_id')
        if type(self.propositions) is not tuple or not 1 <= len(self.propositions) <= 64:
            raise ContractError('INVALID_PROPOSITION_COLLECTION')
        if any(type(p) is not Proposition for p in self.propositions):
            raise ContractError('INVALID_PROPOSITION')
        if len(set(self.propositions)) != len(self.propositions):
            raise ContractError('DUPLICATE_PROPOSITION')


@dataclass(frozen=True, slots=True)
class ReferenceFact:
    reference_id: str
    proposition: Proposition
    citation_ids: tuple[str, ...]

    def __post_init__(self):
        token(self.reference_id, 'reference_id')
        if type(self.proposition) is not Proposition: raise ContractError('INVALID_REFERENCE_PROPOSITION')
        tuple_tokens(self.citation_ids, 'reference.citation_ids', 1, 128)


@dataclass(frozen=True, slots=True)
class Requirement:
    requirement_id: str
    concept_id: str
    facet: str
    description: str
    minimum_depth: int
    weight: int
    critical: bool
    allowed_channels: tuple[str, ...]

    def __post_init__(self):
        for field in ('requirement_id', 'concept_id', 'facet'): token(getattr(self, field), field)
        text(self.description, 'requirement.description', 4096)
        # Engine rubric: 1 mention, 2 explain, 3 apply, 4 derive. Not a claim to
        # implement any external educational taxonomy or validated rating scale.
        integer(self.minimum_depth, 'minimum_depth', 2, 4)
        integer(self.weight, 'weight', 1, 1000)
        if type(self.critical) is not bool: raise ContractError('INVALID_CRITICAL_FLAG')
        tuple_tokens(self.allowed_channels, 'allowed_channels', 1, len(CHANNELS))
        for c in self.allowed_channels: choice(c, CHANNELS, 'allowed_channel')


@dataclass(frozen=True, slots=True)
class CoverageLink:
    link_id: str
    requirement_id: str
    claim_ids: tuple[str, ...]
    depth: int

    def __post_init__(self):
        token(self.link_id, 'link_id'); token(self.requirement_id, 'requirement_id')
        tuple_tokens(self.claim_ids, 'coverage.claim_ids', 1, 128)
        integer(self.depth, 'depth', 1, 4)


@dataclass(frozen=True, slots=True)
class SemanticRequest:
    schema_version: str
    source: SourceRequest
    normalizations: tuple[Normalization, ...]
    references: tuple[ReferenceFact, ...]
    coverage_links: tuple[CoverageLink, ...]

    def __post_init__(self):
        if type(self.schema_version) is not str or self.schema_version != VERSION:
            raise ContractError('UNSUPPORTED_SEMANTIC_SCHEMA')
        if type(self.source) is not SourceRequest: raise ContractError('INVALID_SOURCE_REQUEST')
        records(self.normalizations, Normalization, 'normalizations', 'claim_id')
        records(self.references, ReferenceFact, 'references', 'reference_id')
        records(self.coverage_links, CoverageLink, 'coverage_links', 'link_id')
        n = sum(len(x.propositions) for x in self.normalizations)
        if n > 8192: raise ContractError('TOTAL_PROPOSITION_LIMIT')
        ids = [x.claim_id for x in self.normalizations] + [x.reference_id for x in self.references] + [x.link_id for x in self.coverage_links]
        if len(set(ids)) != len(ids) or 'semantic-scope' in ids:
            raise ContractError('SEMANTIC_SUBJECT_NAMESPACE_COLLISION')
        positions = [(l.requirement_id, tuple(sorted(l.claim_ids))) for l in self.coverage_links]
        if len(set(positions)) != len(positions): raise ContractError('DUPLICATE_COVERAGE_LINK')

    def to_dict(self): return asdict(self)
    @property
    def content_digest(self): return digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class SemanticPolicy:
    """Provision independently of generated request data and submitted receipts."""
    policy_id: str
    source: SourcePolicy
    expected_reference_ids: tuple[str, ...]
    reference_source_ids: tuple[str, ...]
    predicates: tuple[PredicateRule, ...]
    requirements: tuple[Requirement, ...]
    minimum_confidence_ppm: int = 900000
    minimum_weighted_coverage_ppm: int = 1000000
    minimum_independent_assessors: int = 1
    max_receipt_age_seconds: int = 604800
    max_comparisons: int = 100000

    def __post_init__(self):
        token(self.policy_id, 'policy_id')
        if type(self.source) is not SourcePolicy: raise ContractError('INVALID_SOURCE_POLICY')
        tuple_tokens(self.expected_reference_ids, 'expected_reference_ids', 1, MAX_ITEMS)
        tuple_tokens(self.reference_source_ids, 'reference_source_ids', 1, MAX_ITEMS)
        records(self.predicates, PredicateRule, 'predicates', 'predicate_id', 1)
        records(self.requirements, Requirement, 'requirements', 'requirement_id', 1)
        if len({(r.concept_id, r.facet) for r in self.requirements}) != len(self.requirements):
            raise ContractError('DUPLICATE_CONCEPT_FACET')
        integer(self.minimum_confidence_ppm, 'minimum_confidence_ppm', 900000, 1000000)
        integer(self.minimum_weighted_coverage_ppm, 'minimum_weighted_coverage_ppm', 950000, 1000000)
        integer(self.minimum_independent_assessors, 'minimum_independent_assessors', 1, 8)
        integer(self.max_receipt_age_seconds, 'max_receipt_age_seconds', 1, 604800)
        integer(self.max_comparisons, 'max_comparisons', 1, 1000000)

    def to_dict(self): return asdict(self)
    @property
    def content_digest(self): return digest(self.to_dict())
