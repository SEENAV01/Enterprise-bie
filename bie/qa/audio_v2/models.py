"""Audio QA: explicit operator inventory, exact sample clocks and immutable evidence.

UTF-8 offsets count code points, not graphemes. All media intervals are half-open.
PCM support is intentionally bounded; no metadata constitutes acoustic validation.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from ..release_v2.contracts import ArtifactRef, ContractError, token, integer, choice, digest, tuple_tokens, sha256
from ..source_v2.models import Request, Policy, text, records

MAX_SAMPLES=192000*600

def rows(value,cls,name,key,minimum=0,maximum=512):
    records(value,cls,name,key,minimum)
    if len(value)>maximum: raise ContractError('AUDIO_COLLECTION_LIMIT',name)

def ref(value):
    if type(value) is not ArtifactRef or value.size>16*1024*1024: raise ContractError('AUDIO_ARTIFACT_LIMIT_OR_TYPE')

def span(a,b):
    integer(a,'start',0,MAX_SAMPLES);integer(b,'end',a+1,MAX_SAMPLES)

@dataclass(frozen=True,slots=True)
class Narration:
    clip_id: str
    claim_ids: tuple[str,...]
    spoken_text: str
    language: str
    voice_id: str
    start_ms: int
    end_ms: int
    sample_rate: int
    def __post_init__(self):
        for n in ('clip_id','language','voice_id'):token(getattr(self,n),n)
        tuple_tokens(self.claim_ids,'claim_ids',1,128);text(self.spoken_text,'spoken_text',32000)
        integer(self.start_ms,'start_ms',0,3600000);integer(self.end_ms,'end_ms',self.start_ms+1,3600000)
        integer(self.sample_rate,'sample_rate',8000,192000)

@dataclass(frozen=True,slots=True)
class Clip:
    clip_id: str
    wav: ArtifactRef
    timing: ArtifactRef
    start_ms: int
    language: str
    voice_id: str
    def __post_init__(self):
        for n in ('clip_id','language','voice_id'):token(getattr(self,n),n)
        ref(self.wav);ref(self.timing);integer(self.start_ms,'start_ms',0,3600000)

@dataclass(frozen=True,slots=True)
class Word:
    index: int
    start_char: int
    end_char: int
    text: str
    start_sample: int
    end_sample: int
    def __post_init__(self):
        integer(self.index,'index',0,8191);integer(self.start_char,'start_char',0,32000)
        integer(self.end_char,'end_char',self.start_char+1,32000);text(self.text,'word',32000)
        span(self.start_sample,self.end_sample)
        if len(self.text)!=self.end_char-self.start_char:raise ContractError('AUDIO_WORD_TEXT_RANGE')

@dataclass(frozen=True,slots=True)
class TimingReceipt:
    schema_version: str
    clip_id: str
    audio_sha256: str
    transcript_sha256: str
    sample_rate: int
    samples: int
    producer: str
    basis: str
    words: tuple[Word,...]
    def __post_init__(self):
        if self.schema_version!='bie.qa.audio-timing/1':raise ContractError('AUDIO_TIMING_SCHEMA')
        token(self.clip_id,'clip_id');token(self.producer,'producer')
        sha256(self.audio_sha256,'audio_sha256');sha256(self.transcript_sha256,'transcript_sha256')
        integer(self.sample_rate,'sample_rate',8000,192000);integer(self.samples,'samples',1,MAX_SAMPLES)
        choice(self.basis,('engine_events','forced_alignment','human_alignment','reported','synthetic'),'timing.basis')
        rows(self.words,Word,'words','index',1,8192)
        end=0;char=0
        for i,w in enumerate(self.words):
            if w.index!=i or w.start_sample<end or w.end_sample>self.samples or w.start_char<char:raise ContractError('AUDIO_TIMING_ORDER_OR_BOUNDS')
            end=w.end_sample;char=w.end_char

@dataclass(frozen=True,slots=True)
class Cue:
    cue_id: str
    clip_id: str
    word_index: int
    start_ms: int
    end_ms: int
    tolerance_ms: int=100
    def __post_init__(self):
        token(self.cue_id,'cue_id');token(self.clip_id,'clip_id');integer(self.word_index,'word_index',0,8191)
        integer(self.start_ms,'start_ms',0,3600000);integer(self.end_ms,'end_ms',self.start_ms+1,3600000)
        integer(self.tolerance_ms,'tolerance_ms',0,2000)

@dataclass(frozen=True,slots=True)
class CaptionTrack:
    track_id: str
    clip_id: str
    artifact: ArtifactRef
    format: str
    language: str
    def __post_init__(self):
        for n in ('track_id','clip_id','language'):token(getattr(self,n),n)
        ref(self.artifact);choice(self.format,('srt','webvtt'),'format')

@dataclass(frozen=True,slots=True)
class Term:
    term_id: str
    clip_id: str
    start_char: int
    end_char: int
    text: str
    language: str
    allowed_forms: tuple[str,...]
    def __post_init__(self):
        for n in ('term_id','clip_id','language'):token(getattr(self,n),n)
        integer(self.start_char,'start_char',0,32000);integer(self.end_char,'end_char',self.start_char+1,32000)
        text(self.text,'term.text',2048)
        if len(self.text)!=self.end_char-self.start_char:raise ContractError('AUDIO_TERM_TEXT_RANGE')
        if type(self.allowed_forms) is not tuple or not 1<=len(self.allowed_forms)<=32 or len(set(self.allowed_forms))!=len(self.allowed_forms):raise ContractError('AUDIO_ALLOWED_FORMS')
        for f in self.allowed_forms:text(f,'allowed_form',1024)

@dataclass(frozen=True,slots=True)
class PronunciationEvidence:
    clip_id: str
    artifact: ArtifactRef
    def __post_init__(self):token(self.clip_id,'clip_id');ref(self.artifact)

@dataclass(frozen=True,slots=True)
class PronunciationObservation:
    term_id: str
    start_sample: int
    end_sample: int
    heard_form: str
    verdict: str
    def __post_init__(self):
        token(self.term_id,'term_id');span(self.start_sample,self.end_sample);text(self.heard_form,'heard_form',1024)
        choice(self.verdict,('correct','incorrect','uncertain'),'pronunciation.verdict')

@dataclass(frozen=True,slots=True)
class PronunciationReceipt:
    schema_version: str
    clip_id: str
    audio_sha256: str
    transcript_sha256: str
    language: str
    voice_id: str
    basis: str
    observations: tuple[PronunciationObservation,...]
    def __post_init__(self):
        if self.schema_version!='bie.qa.pronunciation/1':raise ContractError('AUDIO_PRONUNCIATION_SCHEMA')
        for n in ('clip_id','language','voice_id'):token(getattr(self,n),n)
        sha256(self.audio_sha256,'audio_sha256');sha256(self.transcript_sha256,'transcript_sha256')
        choice(self.basis,('acoustic_assessment','human_listening','transcript_only','synthetic'),'pronunciation.basis')
        rows(self.observations,PronunciationObservation,'observations','term_id',1)

@dataclass(frozen=True,slots=True)
class AudioRequest:
    schema_version: str
    source: Request
    lesson_id: str
    clips: tuple[Clip,...]
    captions: tuple[CaptionTrack,...]
    pronunciation: tuple[PronunciationEvidence,...]=()
    def __post_init__(self):
        if self.schema_version!='1.0.0' or type(self.source) is not Request:raise ContractError('AUDIO_REQUEST_SCHEMA')
        token(self.lesson_id,'lesson_id');rows(self.clips,Clip,'clips','clip_id',1,32)
        rows(self.captions,CaptionTrack,'captions','track_id',0,64);rows(self.pronunciation,PronunciationEvidence,'pronunciation','clip_id',0,32)
        refs=all_refs(self)
        if len({r.artifact_id for r in refs})!=len(refs) or len({r.path for r in refs})!=len(refs):raise ContractError('AUDIO_DUPLICATE_ARTIFACT')
        if sum(r.size for r in refs)>64*1024*1024:raise ContractError('AUDIO_TOTAL_IO_LIMIT')
    @property
    def content_digest(self):return digest(asdict(self))
    def to_dict(self):return asdict(self)

@dataclass(frozen=True,slots=True)
class AudioPolicy:
    policy_id: str
    source: Policy
    lesson_id: str
    narrations: tuple[Narration,...]
    cues: tuple[Cue,...]
    terms: tuple[Term,...]
    max_caption_chars_per_second: int=24
    max_caption_line_chars: int=48
    max_caption_lines: int=2
    min_caption_ms: int=300
    max_caption_ms: int=8000
    caption_tolerance_ms: int=150
    placement_tolerance_ms: int=20
    max_clipped_ppm: int=1000
    max_receipt_age_seconds: int=3600
    minimum_review_confidence_ppm: int=900000
    minimum_independent_assessors: int=1
    def __post_init__(self):
        token(self.policy_id,'policy_id');token(self.lesson_id,'lesson_id')
        if type(self.source) is not Policy:raise ContractError('AUDIO_SOURCE_POLICY_TYPE')
        rows(self.narrations,Narration,'narrations','clip_id',1,32);rows(self.cues,Cue,'cues','cue_id');rows(self.terms,Term,'terms','term_id')
        for n,a,b in [('max_caption_chars_per_second',1,100),('max_caption_line_chars',1,200),('max_caption_lines',1,6),('min_caption_ms',1,10000),('max_caption_ms',1,30000),('caption_tolerance_ms',0,2000),('placement_tolerance_ms',0,2000),('max_clipped_ppm',0,100000),('max_receipt_age_seconds',1,604800),('minimum_review_confidence_ppm',0,1000000),('minimum_independent_assessors',1,8)]:integer(getattr(self,n),n,a,b)
        if self.min_caption_ms>self.max_caption_ms:raise ContractError('AUDIO_CAPTION_DURATION_POLICY')
        ns={n.clip_id:n for n in self.narrations}
        for c in self.cues:
            if c.clip_id not in ns:raise ContractError('AUDIO_CUE_POLICY_REFERENCE')
        for t in self.terms:
            n=ns.get(t.clip_id)
            if n is None or t.language!=n.language or n.spoken_text[t.start_char:t.end_char]!=t.text:raise ContractError('AUDIO_TERM_POLICY_REFERENCE')
    @property
    def content_digest(self):return digest(asdict(self))

def all_refs(request):
    return tuple([x.artifact for x in request.source.sources]+[x.artifact for x in request.source.outputs]+[a for c in request.clips for a in (c.wav,c.timing)]+[c.artifact for c in request.captions]+[p.artifact for p in request.pronunciation])
