"""Compose VO-001..005 into source-bound narration preparation (not TTS).

No source editing, audio generation, duration claims, timestamp alignment or model
requests happen here. Unknown readings remain explicit review items.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
import unicodedata
from bie.director.speech_timing import SpeechUtterance
from .common import AudioError, Reading, boundary, digest, fingerprint, integer, text
from .segmentation import ProtectedSpan, Pause, SegmentPolicy, SegmentationPlan, split_narration
from .lexicon import Lexicon, matches, resolve
from .symbol_pronunciation import SymbolTable, pronounce_symbol
from .acronym_pronunciation import AcronymTable, pronounce_acronym
from .math_pronunciation import pronounce_math


@dataclass(frozen=True)
class ReadingRequest:
    utterance_id: str
    utterance_fingerprint: str
    start: int
    end: int
    surface: str
    kind: str
    sense: str | None = None
    def __post_init__(self):
        text(self.utterance_id,'utterance',2048);digest(self.utterance_fingerprint)
        integer(self.start,'start');integer(self.end,'end',1);text(self.surface,'surface',8192)
        if self.end<=self.start or self.kind not in ('MATH','SYMBOL','ACRONYM','TERM'):
            raise AudioError('INVALID_READING_REQUEST')
        if self.sense is not None:text(self.sense,'sense',128)


@dataclass(frozen=True)
class AppliedReading:
    utterance_id: str
    start: int
    end: int
    original: str
    reading: Reading


@dataclass(frozen=True)
class SpokenSegment:
    segment_id: str
    display_text: str
    synthesis_text: str
    readings: tuple[AppliedReading,...]
    provider_requirements: tuple[str,...]


@dataclass(frozen=True)
class NarrationPreparation:
    schema_version: str
    segmentation: SegmentationPlan
    lexicon_fingerprint: str
    symbol_table_fingerprint: str
    acronym_table_fingerprint: str
    reading_policy_fingerprint: str
    spoken_segments: tuple[SpokenSegment,...]
    review_reasons: tuple[str,...]
    preparation_passed: bool
    tts_request_ready: bool = False
    audio_generated: bool = False
    audio_verified: bool = False
    product_accepted: bool = False
    def fingerprint(self):return fingerprint(self)


def inline_math_requests(utterances: tuple[SpeechUtterance,...]) -> tuple[ReadingRequest,...]:
    """Only explicit \\( ... \\) markers are auto-read. Dollar amounts are not guessed."""
    out=[]
    for u in utterances:
        i=0
        while i<len(u.text):
            start=u.text.find(r'\(',i)
            stray=u.text.find(r'\)',i)
            if stray>=0 and (start<0 or stray<start):raise AudioError('UNBALANCED_MATH_MARKER',u.utterance_id)
            if start<0:break
            end=u.text.find(r'\)',start+2)
            if end<0 or r'\(' in u.text[start+2:end]:raise AudioError('UNBALANCED_MATH_MARKER',u.utterance_id)
            end+=2
            out.append(ReadingRequest(u.utterance_id,u.fingerprint(),start,end,u.text[start:end],'MATH'))
            i=end
    return tuple(out)


def prepare_narration(utterances: tuple[SpeechUtterance,...], *, lexicon:Lexicon, symbols:SymbolTable,
                      acronyms:AcronymTable, requests:tuple[ReadingRequest,...]=(),
                      pauses:tuple[Pause,...]=(), policy:SegmentPolicy=SegmentPolicy(), domain='general',
                      allow_primary_language=False, auto_inline_math=True) -> NarrationPreparation:
    if type(utterances)is not tuple or type(requests)is not tuple or len(requests)>10000 or any(type(r)is not ReadingRequest for r in requests):
        raise AudioError('INVALID_PREPARATION_INPUT')
    if type(lexicon)is not Lexicon or type(symbols)is not SymbolTable or type(acronyms)is not AcronymTable:
        raise AudioError('PRONUNCIATION_TABLE_REQUIRED')
    text(domain,'domain',128)
    if type(auto_inline_math)is not bool or type(allow_primary_language)is not bool:raise AudioError('INVALID_POLICY_FLAG')
    # First validate every input with the canonical segmentation boundary.
    for u in utterances:
        if type(u)is not SpeechUtterance:raise AudioError('CANONICAL_UTTERANCE_REQUIRED')
        text(u.text,'narration',1000000)
    by_id={u.utterance_id:u for u in utterances}
    explicit=list(requests)
    if auto_inline_math:
        for r in inline_math_requests(utterances):
            prior=[x for x in requests if x.utterance_id==r.utterance_id and x.start<r.end and r.start<x.end]
            if prior:
                if len(prior)!=1 or prior[0]!=r:raise AudioError('CONFLICTING_INLINE_READING')
            else:explicit.append(r)
    for r in explicit:
        if type(r)is not ReadingRequest or r.utterance_id not in by_id:raise AudioError('UNKNOWN_READING_UTTERANCE')
        u=by_id[r.utterance_id]
        if r.utterance_fingerprint!=u.fingerprint():raise AudioError('STALE_READING_REQUEST')
        if r.end>len(u.text) or u.text[r.start:r.end]!=r.surface:raise AudioError('READING_TEXT_MISMATCH')
        if not boundary(u.text,r.start) or not boundary(u.text,r.end):raise AudioError('READING_GRAPHEME_SPLIT')
    readings=[];reasons=[];protected=[]
    for u in utterances:
        owned=sorted((r for r in explicit if r.utterance_id==u.utterance_id),key=lambda r:r.start)
        if any(a.end>b.start for a,b in zip(owned,owned[1:])):raise AudioError('OVERLAPPING_READINGS')
        # Scoped dictionary matching runs only on ranges not explicitly owned.
        ends=[0]+[r.end for r in owned];starts=[r.start for r in owned]+[len(u.text)]
        auto=[]
        for lo,hi in zip(ends,starts):
            if lo>=hi or not u.text[lo:hi].strip():continue
            for a,b,reading in matches(lexicon,u.text[lo:hi],u.language,domain=domain,allow_primary_language=allow_primary_language):
                # Verify against the full string as well as this slice.
                from .common import is_word
                a+=lo;b+=lo
                if a and is_word(u.text[a-1]) and is_word(u.text[a]):continue
                if b<len(u.text) and is_word(u.text[b-1]) and is_word(u.text[b]):continue
                auto.append((a,b,reading))
        occupied=[(r.start,r.end) for r in owned]+[(a,b) for a,b,_ in auto]
        # Uppercase candidates are never silently given an invented expansion.
        for m in re.finditer(r'(?<!\w)(?:(?:[A-Z]\.){2,16}|[A-Z]{2,16})(?!\w)',u.text):
            if any(a<m.end() and m.start()<b for a,b in occupied):continue
            try:reading=pronounce_acronym(m.group(),u.language,acronyms,domain=domain)
            except AudioError as exc:
                if exc.code!='ACRONYM_NOT_FOUND':raise
                reasons.append(f'UNRESOLVED_ACRONYM:{u.utterance_id}:{m.start()}:{m.group()}');continue
            auto.append((m.start(),m.end(),reading));occupied.append(m.span())
        for r in owned:
            if r.kind=='MATH':
                expression=r.surface[2:-2] if r.surface.startswith(r'\(') and r.surface.endswith(r'\)') else r.surface
                reading=pronounce_math(expression,u.language,evidence_refs=u.evidence_ids).reading
            elif r.kind=='TERM':reading=resolve(lexicon,r.surface,u.language,domain=domain,sense=r.sense,allow_primary_language=allow_primary_language)
            elif r.kind=='SYMBOL':reading=pronounce_symbol(r.surface,u.language,symbols,domain=domain,sense=r.sense)
            else:reading=pronounce_acronym(r.surface,u.language,acronyms,domain=domain)
            auto.append((r.start,r.end,reading))
        auto.sort(key=lambda x:x[0])
        if any(a[1]>b[0] for a,b in zip(auto,auto[1:])):raise AudioError('READING_OWNERSHIP_COLLISION')
        for a,b,r in auto:
            readings.append(AppliedReading(u.utterance_id,a,b,u.text[a:b],r))
            protected.append(ProtectedSpan(u.utterance_id,a,b,u.text[a:b],u.fingerprint(),r.kind.lower()))
        mask=list(u.text)
        for a,b,_ in auto:mask[a:b]=' '*(b-a)
        remainder=''.join(mask)
        if (re.search(r'[=+*/^_<>$%≤≥≠≈±\\]|\d',remainder) or any(unicodedata.category(c) in ('Sm','Sc','So') or c == 'µ' or 'GREEK' in unicodedata.name(c,'') for c in remainder)):
            reasons.append(f'UNRESOLVED_NUMERIC_OR_SYMBOLIC_TEXT:{u.utterance_id}')
        reasons.extend(f'UPSTREAM:{u.utterance_id}:{reason}' for reason in u.review_reasons)
    plan=split_narration(utterances,policy=policy,protected=tuple(protected),pauses=pauses)
    spoken=[]
    for s in plan.segments:
        own=tuple(r for r in readings if r.utterance_id==s.utterance_id and s.start_char<=r.start and r.end<=s.end_char)
        cursor=s.start_char;parts=[];requirements=set()
        for r in own:
            parts.append(by_id[s.utterance_id].text[cursor:r.start]);parts.append(r.reading.spoken);cursor=r.end
            if r.reading.phonemes is not None:requirements.add('phoneme:'+r.reading.alphabet)
        parts.append(by_id[s.utterance_id].text[cursor:s.end_char])
        synthesis=''.join(parts)
        if len(synthesis)>65536:raise AudioError('REALIZED_SPEECH_BUDGET',s.segment_id)
        if len(synthesis)>policy.max_chars or len(synthesis.encode('utf-8'))>policy.max_utf8_bytes:
            reasons.append(f'REALIZED_SEGMENT_EXCEEDS_REQUEST_LIMIT:{s.segment_id}')
        spoken.append(SpokenSegment(s.segment_id,s.display_text,synthesis,own,tuple(sorted(requirements))))
    return NarrationPreparation('bie.audio.preparation/1',plan,lexicon.fingerprint(),symbols.fingerprint(),acronyms.fingerprint(),
        fingerprint({'math':'bie-math-reading/1','domain':domain,'allow_primary_language':allow_primary_language,'auto_inline_math':auto_inline_math}),
        tuple(spoken),tuple(sorted(set(reasons))),not reasons)


def validate_preparation(record,utterances,**options):
    if type(record)is not NarrationPreparation:raise AudioError('PREPARATION_REQUIRED')
    if record!=prepare_narration(utterances,**options):raise AudioError('STALE_OR_EDITED_PREPARATION')
    return record
