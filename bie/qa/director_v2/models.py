"""Bounded director QA records. Policies/trust are operator-owned, never candidate-owned.

Times are declared milliseconds. Text identities reference the source_v2 byte/span
contract. None of these records is an observation of audio, pixels or learning.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from ..release_v2.contracts import ContractError, token, integer, choice, tuple_tokens, digest
from ..source_v2.models import Request, Policy, text, records

MAX_SCENES = 256
MAX_BEATS = 1024
MAX_ROUTES = 32
MAX_MS = 86_400_000
ROLES = ('hook', 'orientation', 'problem', 'explanation', 'demonstration', 'transition',
         'payoff', 'recap', 'retrieval', 'feedback', 'emphasis', 'handoff', 'pause')
CHANNELS = ('narration', 'dialogue', 'on_screen', 'pause')
MODES = ('quote', 'paraphrase', 'simplification', 'analogy', 'hypothetical', 'question', 'instruction')


def rows(value, cls, label, key, minimum=0, maximum=MAX_BEATS):
    records(value, cls, label, key, minimum)
    if len(value) > maximum:
        raise ContractError('DIR_COLLECTION_LIMIT', label)


def boolean(value, label):
    if type(value) is not bool:
        raise ContractError('DIR_BOOLEAN_REQUIRED', label)


@dataclass(frozen=True, slots=True)
class Scene:
    scene_id: str
    role: str
    purpose: str
    objective_ids: tuple[str, ...]
    parent_scene_ids: tuple[str, ...]
    duration_ms: int
    def __post_init__(self):
        token(self.scene_id, 'scene_id'); choice(self.role, ROLES, 'scene.role')
        text(self.purpose, 'scene.purpose', 4096)
        tuple_tokens(self.objective_ids, 'objectives', 1, 128)
        tuple_tokens(self.parent_scene_ids, 'parents', 0, MAX_SCENES)
        integer(self.duration_ms, 'duration_ms', 1, MAX_MS)


@dataclass(frozen=True, slots=True)
class Beat:
    beat_id: str
    scene_id: str
    role: str
    channel: str
    start_ms: int
    end_ms: int
    claim_ids: tuple[str, ...]
    objective_ids: tuple[str, ...]
    speaker_id: str = 'narrator'
    voice_id: str = 'default'
    repeat_of: tuple[str, ...] = ()
    def __post_init__(self):
        for k in ('beat_id', 'scene_id', 'speaker_id', 'voice_id'): token(getattr(self, k), k)
        choice(self.role, ROLES, 'beat.role'); choice(self.channel, CHANNELS, 'beat.channel')
        integer(self.start_ms, 'start_ms', 0, MAX_MS)
        integer(self.end_ms, 'end_ms', self.start_ms + 1, MAX_MS)
        tuple_tokens(self.claim_ids, 'beat.claims', 0 if self.channel == 'pause' else 1, 128)
        tuple_tokens(self.objective_ids, 'beat.objectives', 0, 128)
        tuple_tokens(self.repeat_of, 'repeat_of', 0, 32)
        if (self.channel == 'pause') != (self.role == 'pause') or (self.channel == 'pause' and self.claim_ids):
            raise ContractError('DIR_PAUSE_CANNOT_HIDE_TEXT')


@dataclass(frozen=True, slots=True)
class Route:
    route_id: str
    scene_ids: tuple[str, ...]
    def __post_init__(self):
        token(self.route_id, 'route_id'); tuple_tokens(self.scene_ids, 'route.scenes', 1, MAX_SCENES)


@dataclass(frozen=True, slots=True)
class Transition:
    transition_id: str
    from_scene_id: str
    to_scene_id: str
    claim_ids: tuple[str, ...]
    def __post_init__(self):
        for k in ('transition_id', 'from_scene_id', 'to_scene_id'): token(getattr(self, k), k)
        tuple_tokens(self.claim_ids, 'transition.claims', 1, 128)
        if self.from_scene_id == self.to_scene_id: raise ContractError('DIR_SELF_TRANSITION')


@dataclass(frozen=True, slots=True)
class Promise:
    promise_id: str
    setup_beat_id: str
    payoff_beat_ids: tuple[str, ...]
    def __post_init__(self):
        token(self.promise_id, 'promise_id'); token(self.setup_beat_id, 'setup_beat_id')
        tuple_tokens(self.payoff_beat_ids, 'payoffs', 1, 32)


@dataclass(frozen=True, slots=True)
class TermIntroduction:
    introduction_id: str
    term_id: str
    beat_id: str
    def __post_init__(self):
        for k in ('introduction_id', 'term_id', 'beat_id'): token(getattr(self, k), k)


@dataclass(frozen=True, slots=True)
class SpokenForm:
    beat_id: str
    text: str
    claim_ids: tuple[str, ...] = ()
    def __post_init__(self):
        token(self.beat_id, 'beat_id'); text(self.text, 'spoken_form.text', 100000)
        tuple_tokens(self.claim_ids, 'spoken_form.claim_ids', 0, 128)


@dataclass(frozen=True, slots=True)
class ConditionWitness:
    condition_id: str
    claim_id: str
    def __post_init__(self):
        token(self.condition_id, 'condition_id'); token(self.claim_id, 'claim_id')


@dataclass(frozen=True, slots=True)
class FidelityMapping:
    mapping_id: str
    claim_id: str
    mode: str
    citation_ids: tuple[str, ...]
    facet_ids: tuple[str, ...]
    conditions: tuple[ConditionWitness, ...] = ()
    disclosure_claim_ids: tuple[str, ...] = ()
    def __post_init__(self):
        token(self.mapping_id, 'mapping_id'); token(self.claim_id, 'claim_id')
        choice(self.mode, MODES, 'fidelity.mode')
        tuple_tokens(self.citation_ids, 'fidelity.citations', 0, 128)
        tuple_tokens(self.facet_ids, 'fidelity.facets', 0, 128)
        rows(self.conditions, ConditionWitness, 'conditions', 'condition_id', 0, 128)
        tuple_tokens(self.disclosure_claim_ids, 'disclosures', 0, 128)


@dataclass(frozen=True, slots=True)
class DirectorRequest:
    schema_version: str
    source: Request
    lesson_id: str
    audience_id: str
    language: str
    scenes: tuple[Scene, ...]
    beats: tuple[Beat, ...]
    routes: tuple[Route, ...]
    transitions: tuple[Transition, ...]
    promises: tuple[Promise, ...]
    term_introductions: tuple[TermIntroduction, ...]
    spoken_forms: tuple[SpokenForm, ...]
    fidelity: tuple[FidelityMapping, ...]
    def __post_init__(self):
        if self.schema_version != '1.0.0': raise ContractError('DIR_SCHEMA_VERSION')
        if type(self.source) is not Request: raise ContractError('DIR_SOURCE_REQUIRED')
        for k in ('lesson_id', 'audience_id', 'language'): token(getattr(self, k), k)
        specs = [('scenes', Scene, 'scene_id', MAX_SCENES), ('beats', Beat, 'beat_id', MAX_BEATS),
                 ('routes', Route, 'route_id', MAX_ROUTES), ('transitions', Transition, 'transition_id', MAX_BEATS),
                 ('promises', Promise, 'promise_id', 128), ('term_introductions', TermIntroduction, 'introduction_id', MAX_BEATS),
                 ('spoken_forms', SpokenForm, 'beat_id', MAX_BEATS), ('fidelity', FidelityMapping, 'mapping_id', 4096)]
        for name, cls, key, maximum in specs: rows(getattr(self, name), cls, name, key, 0, maximum)
        ids = ['director-scope', 'pacing-profile']
        for name, cls, key, _ in specs:
            if name != 'spoken_forms': ids.extend(getattr(x, key) for x in getattr(self, name))
        if len(ids) != len(set(ids)): raise ContractError('DIR_CROSS_COLLECTION_ID_COLLISION')
        if len({x.claim_id for x in self.fidelity}) != len(self.fidelity): raise ContractError('DIR_DUPLICATE_FIDELITY_CLAIM')
        if len({(x.term_id, x.beat_id) for x in self.term_introductions}) != len(self.term_introductions):
            raise ContractError('DIR_DUPLICATE_TERM_INTRODUCTION')
        if sum(len(x.text) for x in self.spoken_forms) > 4_000_000: raise ContractError('DIR_SPOKEN_TEXT_LIMIT')
    def to_dict(self): return asdict(self)
    @property
    def content_digest(self): return digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class SceneRequirement:
    scene_id: str
    objective_ids: tuple[str, ...]
    parent_scene_ids: tuple[str, ...]
    allowed_roles: tuple[str, ...]
    def __post_init__(self):
        token(self.scene_id, 'scene_id')
        tuple_tokens(self.objective_ids, 'objectives', 1, 128)
        tuple_tokens(self.parent_scene_ids, 'parents', 0, MAX_SCENES)
        tuple_tokens(self.allowed_roles, 'allowed_roles', 1, len(ROLES))
        for role in self.allowed_roles: choice(role, ROLES, 'scene role')


@dataclass(frozen=True, slots=True)
class RouteRequirement:
    route_id: str
    scene_ids: tuple[str, ...]
    objective_ids: tuple[str, ...]
    facet_ids: tuple[str, ...]
    opening_roles: tuple[str, ...] = ('hook', 'orientation')
    closing_roles: tuple[str, ...] = ('recap', 'handoff')
    max_duration_ms: int = 3600000
    def __post_init__(self):
        token(self.route_id, 'route_id')
        for k, n in (('scene_ids', MAX_SCENES), ('objective_ids', 128), ('facet_ids', 128)):
            tuple_tokens(getattr(self, k), k, 1, n)
        for k in ('opening_roles', 'closing_roles'):
            tuple_tokens(getattr(self, k), k, 1, len(ROLES))
            for role in getattr(self, k): choice(role, ROLES, k)
        integer(self.max_duration_ms, 'max_duration_ms', 1, MAX_MS)


@dataclass(frozen=True, slots=True)
class TermRequirement:
    term_id: str
    forms: tuple[str, ...]
    assumed_known: bool = False
    def __post_init__(self):
        token(self.term_id, 'term_id'); boolean(self.assumed_known, 'assumed_known')
        if type(self.forms) is not tuple or not 1 <= len(self.forms) <= 16: raise ContractError('DIR_TERM_FORMS')
        for v in self.forms: text(v, 'term_form', 256)
        if len(set(self.forms)) != len(self.forms): raise ContractError('DIR_DUPLICATE_TERM_FORM')


@dataclass(frozen=True, slots=True)
class FacetRequirement:
    facet_id: str
    citation_ids: tuple[str, ...]
    condition_ids: tuple[str, ...] = ()
    allowed_modes: tuple[str, ...] = ('quote', 'paraphrase', 'simplification')
    def __post_init__(self):
        token(self.facet_id, 'facet_id'); tuple_tokens(self.citation_ids, 'facet citations', 1, 128)
        tuple_tokens(self.condition_ids, 'facet conditions', 0, 128)
        tuple_tokens(self.allowed_modes, 'allowed_modes', 1, len(MODES))
        for mode in self.allowed_modes: choice(mode, MODES, 'facet mode')


@dataclass(frozen=True, slots=True)
class TimingConstraint:
    constraint_id: str
    before_beat_id: str
    after_beat_id: str
    minimum_gap_ms: int
    maximum_gap_ms: int
    def __post_init__(self):
        for k in ('constraint_id', 'before_beat_id', 'after_beat_id'): token(getattr(self, k), k)
        integer(self.minimum_gap_ms, 'minimum_gap_ms', 0, MAX_MS)
        integer(self.maximum_gap_ms, 'maximum_gap_ms', self.minimum_gap_ms, MAX_MS)
        if self.before_beat_id == self.after_beat_id: raise ContractError('DIR_SELF_TIMING_CONSTRAINT')


@dataclass(frozen=True, slots=True)
class PacingLimits:
    speech_codepoints_per_minute: int = 1200
    screen_codepoints_per_minute: int = 1800
    max_concurrent_speech: int = 1
    max_unmotivated_gap_ms: int = 4000
    max_pause_ms: int = 30000
    max_sentence_codepoints: int = 300
    qualification_window_ms: int = 15000
    def __post_init__(self):
        for k in ('speech_codepoints_per_minute', 'screen_codepoints_per_minute'):
            integer(getattr(self, k), k, 1, 100000)
        integer(self.max_concurrent_speech, 'max_concurrent_speech', 1, 4)
        for k in ('max_unmotivated_gap_ms', 'max_pause_ms', 'qualification_window_ms'):
            integer(getattr(self, k), k, 0, 600000)
        integer(self.max_sentence_codepoints, 'max_sentence_codepoints', 1, 10000)


@dataclass(frozen=True, slots=True)
class DirectorPolicy:
    policy_id: str
    source: Policy
    lesson_id: str
    audience_id: str
    language: str
    scenes: tuple[SceneRequirement, ...]
    routes: tuple[RouteRequirement, ...]
    terms: tuple[TermRequirement, ...]
    facets: tuple[FacetRequirement, ...]
    expected_promise_ids: tuple[str, ...]
    timing_constraints: tuple[TimingConstraint, ...]
    pacing: PacingLimits = PacingLimits()
    minimum_independent_assessors: int = 1
    minimum_review_confidence_ppm: int = 900000
    max_receipt_age_seconds: int = 86400
    def __post_init__(self):
        for k in ('policy_id', 'lesson_id', 'audience_id', 'language'): token(getattr(self, k), k)
        if type(self.source) is not Policy or type(self.pacing) is not PacingLimits: raise ContractError('DIR_POLICY_COMPONENT_TYPE')
        rows(self.scenes, SceneRequirement, 'scenes', 'scene_id', 1, MAX_SCENES)
        rows(self.routes, RouteRequirement, 'routes', 'route_id', 1, MAX_ROUTES)
        rows(self.terms, TermRequirement, 'terms', 'term_id', 0, 128)
        rows(self.facets, FacetRequirement, 'facets', 'facet_id', 1, 128)
        rows(self.timing_constraints, TimingConstraint, 'timing', 'constraint_id', 0, MAX_BEATS)
        tuple_tokens(self.expected_promise_ids, 'promise_ids', 0, 128)
        integer(self.minimum_independent_assessors, 'minimum_independent_assessors', 1, 8)
        integer(self.minimum_review_confidence_ppm, 'minimum_review_confidence_ppm', 900000, 1000000)
        integer(self.max_receipt_age_seconds, 'max_receipt_age_seconds', 1, 604800)
        ss = {s.scene_id for s in self.scenes}; oo = {o for s in self.scenes for o in s.objective_ids}; ff = {f.facet_id for f in self.facets}
        for s in self.scenes:
            if not set(s.parent_scene_ids) <= ss or s.scene_id in s.parent_scene_ids: raise ContractError('DIR_POLICY_PARENT_INVALID')
        for r in self.routes:
            if not set(r.scene_ids) <= ss or not set(r.objective_ids) <= oo or not set(r.facet_ids) <= ff:
                raise ContractError('DIR_POLICY_ROUTE_REFERENCE')
        if {sid for r in self.routes for sid in r.scene_ids} != ss: raise ContractError('DIR_POLICY_UNREACHABLE_SCENE')
        if {fid for r in self.routes for fid in r.facet_ids} != ff: raise ContractError('DIR_POLICY_UNASSIGNED_FACET')
    @property
    def content_digest(self): return digest(asdict(self))
