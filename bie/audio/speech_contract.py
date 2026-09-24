"""VO-006/007 immutable text-to-speech handoff, retaining source offsets.

A content fingerprint is an identity, not a factual or acoustic certificate.
Python code points, half-open source spans, integer sample counts at media boundaries.
"""
from __future__ import annotations
from dataclasses import dataclass
from .common import AudioError, boundary, digest, fingerprint, integer, locale, refs, text


def literal(value: str, name: str, maximum: int = 65536) -> str:
    if type(value) is not str or not value or len(value)>maximum:
        raise AudioError('INVALID_LITERAL',name)
    text('x'+value,name,maximum+1)  # allow whitespace, not invalid code points
    return value


def records(value, cls, name, limit=10000, required=True):
    if type(value) is not tuple or len(value)>limit or (required and not value) or any(type(x) is not cls for x in value):
        raise AudioError('INVALID_RECORDS',name)
    return value


@dataclass(frozen=True)
class SpeechSpan:
    start: int
    end: int
    original: str
    spoken: str
    language: str
    rule_fingerprint: str
    source_refs: tuple[str,...]
    kind: str = 'literal'
    phonemes: str | None = None
    alphabet: str | None = None
    def __post_init__(self):
        integer(self.start,'source start');integer(self.end,'source end',1)
        if self.end-self.start!=len(self.original):raise AudioError('SPAN_LENGTH')
        literal(self.original,'source',1000000);literal(self.spoken,'speech')
        locale(self.language);digest(self.rule_fingerprint);refs(self.source_refs,'speech refs')
        text(self.kind,'kind',64)
        if self.kind=='literal' and (self.original!=self.spoken or self.phonemes is not None):raise AudioError('LITERAL_CHANGED')
        if (self.phonemes is None)!=(self.alphabet is None):raise AudioError('PHONEME_PAIR')
        if self.phonemes is not None:
            text(self.phonemes,'phonemes',4096)
            if self.alphabet!='ipa':raise AudioError('PHONEME_ALPHABET')


@dataclass(frozen=True)
class SpeechSegment:
    segment_id: str
    utterance_id: str
    utterance_fingerprint: str
    script_fingerprint: str
    scene_id: str
    persona_id: str
    language: str
    start: int
    end: int
    display_text: str
    spans: tuple[SpeechSpan,...]
    objective_ids: tuple[str,...]
    pause_after_ms: int = 0
    pause_refs: tuple[str,...] = ()
    def __post_init__(self):
        for k in ('segment_id','utterance_id','scene_id','persona_id'):text(getattr(self,k),k,2048)
        digest(self.utterance_fingerprint);digest(self.script_fingerprint);locale(self.language)
        literal(self.display_text,'display',1000000);integer(self.start,'start');integer(self.end,'end',1)
        refs(self.objective_ids,'objectives');records(self.spans,SpeechSpan,'spans')
        integer(self.pause_after_ms,'pause',0,3600000);refs(self.pause_refs,'pause refs',bool(self.pause_after_ms))
        position=self.start
        for span in self.spans:
            if span.start!=position:raise AudioError('SOURCE_MAP_GAP')
            a,b=span.start-self.start,span.end-self.start
            if self.display_text[a:b]!=span.original:raise AudioError('SOURCE_MAP_TEXT')
            if not boundary(self.display_text,a) or not boundary(self.display_text,b):raise AudioError('SOURCE_MAP_CLUSTER')
            position=span.end
        if position!=self.end or self.end-self.start!=len(self.display_text):raise AudioError('SOURCE_MAP_COVERAGE')
    @property
    def spoken_text(self):return ''.join(x.spoken for x in self.spans)
    @property
    def languages(self):return tuple(sorted({s.language for s in self.spans if s.spoken.strip()}))
    def fingerprint(self):return fingerprint(self)


@dataclass(frozen=True)
class SpeechPlan:
    profile: str
    preparation_fingerprint: str
    language_policy_fingerprint: str
    segments: tuple[SpeechSegment,...]
    review_reasons: tuple[str,...] = ()
    schema_version: str = 'bie.audio.speech-plan/1'
    def __post_init__(self):
        if self.profile not in ('batch001-144','batch001-204') or self.schema_version!='bie.audio.speech-plan/1':raise AudioError('SPEECH_PROFILE')
        digest(self.preparation_fingerprint);digest(self.language_policy_fingerprint)
        records(self.segments,SpeechSegment,'segments');refs(self.review_reasons,'reviews',False)
        if len({s.segment_id for s in self.segments})!=len(self.segments):raise AudioError('DUPLICATE_SEGMENT')
        if len({s.script_fingerprint for s in self.segments})!=1:raise AudioError('MIXED_SCRIPT_REVISIONS')
        closed=set();current=None;position=0;bindings={}
        for s in self.segments:
            binding=(s.utterance_fingerprint,s.script_fingerprint,s.scene_id,s.persona_id,s.language)
            if s.utterance_id in bindings and bindings[s.utterance_id]!=binding:raise AudioError('UTTERANCE_BINDING_CHANGED')
            bindings[s.utterance_id]=binding
            if s.utterance_id!=current:
                if s.utterance_id in closed:raise AudioError('UTTERANCE_ORDER')
                closed.add(s.utterance_id);current=s.utterance_id;position=0
            if s.start!=position:raise AudioError('SEGMENT_GAP')
            position=s.end
        if sum(len(s.spoken_text.encode('utf-8')) for s in self.segments)>8000000:raise AudioError('SPEECH_PLAN_BUDGET')
    def fingerprint(self):return fingerprint(self)
    def require_ready(self):
        if self.review_reasons:raise AudioError('UPSTREAM_REVIEW_REQUIRED',';'.join(self.review_reasons)[:300])
        return self
