"""AUDIO SYNC-001..005 shared sample-clock contracts.

Engine onsets are measurements, not independently verified phonetic word ends.
All ranges are half-open. No float arithmetic determines a media boundary.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib, unicodedata
from .common import AudioError, boundary, digest, fingerprint, integer, refs, text
from .speech_contract import SpeechSegment, records
from .tts_generation import SpeechAsset
from .pcm_audio import validate_wav

MAX_SAMPLES = 192000 * 1800


def samples_for_ms(ms: int, rate: int) -> int:
    integer(ms, 'milliseconds', 0, 1800000)
    integer(rate, 'sample rate', 8000, 192000)
    return (ms * rate + 500) // 1000


def ceil_div(a: int, b: int) -> int:
    return -(-a // b)


@dataclass(frozen=True)
class FrameRate:
    numerator: int = 30
    denominator: int = 1
    def __post_init__(self):
        integer(self.numerator, 'fps numerator', 1, 240000)
        integer(self.denominator, 'fps denominator', 1, 10000)
        value = Fraction(self.numerator, self.denominator)
        if not 1 <= value <= 240 or value.numerator != self.numerator or value.denominator != self.denominator:
            raise AudioError('FRAME_RATE_NOT_CANONICAL')
    def at_or_after(self, sample: int, rate: int) -> int:
        integer(sample, 'sample', 0, MAX_SAMPLES); integer(rate, 'sample rate', 8000, 192000)
        return ceil_div(sample * self.numerator, rate * self.denominator)
    def sample_at(self, frame: int, rate: int) -> int:
        integer(frame, 'frame', 0, 432000); integer(rate, 'sample rate', 8000, 192000)
        return frame * rate * self.denominator // self.numerator


@dataclass(frozen=True)
class SourceSlice:
    start: int
    end: int
    original: str
    rule_fingerprint: str
    source_refs: tuple[str, ...]
    mapping: str
    def __post_init__(self):
        integer(self.start, 'source start'); integer(self.end, 'source end', 1)
        if self.end - self.start != len(self.original) or not self.original:
            raise AudioError('TIMING_SOURCE_RANGE')
        digest(self.rule_fingerprint); refs(self.source_refs, 'source refs')
        if self.mapping not in ('literal_offset', 'whole_transformed_span'):
            raise AudioError('TIMING_SOURCE_MAPPING')


def source_slices(segment: SpeechSegment, start: int, end: int) -> tuple[SourceSlice, ...]:
    integer(start, 'spoken start'); integer(end, 'spoken end', 1)
    value = segment.spoken_text
    if end > len(value) or end <= start or not boundary(value, start) or not boundary(value, end):
        raise AudioError('TIMING_SPOKEN_RANGE')
    cursor = 0; out = []
    for span in segment.spans:
        stop = cursor + len(span.spoken)
        a, b = max(start, cursor), min(end, stop)
        if a < b:
            if span.kind == 'literal':
                sa, sb = span.start + a-cursor, span.start + b-cursor
                original = span.original[a-cursor:b-cursor]; mode = 'literal_offset'
            else:
                sa, sb, original, mode = span.start, span.end, span.original, 'whole_transformed_span'
            out.append(SourceSlice(sa, sb, original, span.rule_fingerprint, span.source_refs, mode))
        cursor = stop
    return tuple(out)


def significant(char: str) -> bool:
    return unicodedata.category(char)[0] in 'LMN' or unicodedata.category(char) in ('Sm', 'So', 'Sc')


@dataclass(frozen=True)
class WordStamp:
    index: int
    spoken_start: int
    spoken_end: int
    spoken: str
    start_sample: int
    end_sample: int
    source: tuple[SourceSlice, ...]
    end_basis: str = 'NEXT_ONSET_OR_CLAUSE_EVENT'
    def __post_init__(self):
        integer(self.index, 'word index', 0, 19999)
        integer(self.spoken_start, 'spoken start'); integer(self.spoken_end, 'spoken end', 1)
        text(self.spoken, 'timed word', 65536)
        if self.spoken_end - self.spoken_start != len(self.spoken): raise AudioError('WORD_TEXT_RANGE')
        integer(self.start_sample, 'word start', 0, MAX_SAMPLES)
        integer(self.end_sample, 'word end', 1, MAX_SAMPLES)
        if self.end_sample <= self.start_sample: raise AudioError('WORD_TIME_RANGE')
        records(self.source, SourceSlice, 'word source')
        if self.end_basis not in ('NEXT_ONSET_OR_CLAUSE_EVENT', 'ENGINE_MARK_BOUNDARY', 'REPORTED_INTERVAL'):
            raise AudioError('WORD_END_BASIS')


@dataclass(frozen=True)
class AlignedSpeech:
    request_fingerprint: str
    media_sha256: str
    segment_fingerprint: str
    runtime_fingerprint: str
    producer_fingerprint: str
    event_fingerprint: str
    sample_rate: int
    provider_samples: int
    pause_samples: int
    words: tuple[WordStamp, ...]
    basis: str
    schema_version: str = 'bie.audio.word-timing/1'
    def __post_init__(self):
        for value in (self.request_fingerprint, self.segment_fingerprint, self.runtime_fingerprint,
                      self.producer_fingerprint, self.event_fingerprint): digest(value)
        if len(self.media_sha256) != 64 or any(x not in '0123456789abcdef' for x in self.media_sha256):
            raise AudioError('TIMING_MEDIA_HASH')
        integer(self.sample_rate, 'sample rate', 8000, 192000)
        integer(self.provider_samples, 'provider samples', 1, MAX_SAMPLES)
        integer(self.pause_samples, 'pause samples', 0, MAX_SAMPLES)
        records(self.words, WordStamp, 'words', limit=20000)
        if self.basis not in ('ESPEAK_ENGINE_EVENTS_PCM_REPLAY', 'ESPEAK_MARK_EVENTS_SAME_PCM', 'REPORTED_UNVERIFIED', 'SYNTHETIC_TEST_DOUBLE', 'ELEVENLABS_CHARACTER_EVENTS_SAME_RESPONSE', 'NEURAL_CHARACTER_FIXTURE_SAME_PCM'):
            raise AudioError('TIMING_BASIS')
        if self.schema_version != 'bie.audio.word-timing/1': raise AudioError('TIMING_SCHEMA')
        end = -1; char_end = 0
        for i, word in enumerate(self.words):
            if word.index != i or word.start_sample < end or word.end_sample > self.provider_samples or word.spoken_start < char_end:
                raise AudioError('TIMING_ORDER_OR_BOUNDS')
            end = word.end_sample; char_end = word.spoken_end
    def fingerprint(self): return fingerprint(self)
    @property
    def total_samples(self): return self.provider_samples + self.pause_samples
    def receipt(self):
        return {**asdict(self), 'fingerprint': self.fingerprint(),
                'timing_resolution': ('provider decimal seconds converted half-up to samples'
                    if self.basis == 'ELEVENLABS_CHARACTER_EVENTS_SAME_RESPONSE' else
                    'synthetic response fixture seconds converted half-up to samples, NOT live speech'
                    if self.basis == 'NEURAL_CHARACTER_FIXTURE_SAME_PCM' else
                    'provider public integer milliseconds converted half-up to samples'),
                'word_end_semantics': 'provider boundary/display window, NOT independently detected phonetic offset'
                    if 'NEURAL_' in self.basis or self.basis.startswith('ELEVENLABS_') else
                    'engine source-boundary/display window, NOT independently detected phonetic offset',
                'acoustic_alignment_verified': False, 'pronunciation_verified': False,
                'product_accepted': False}


def validate_asset(asset: SpeechAsset):
    if type(asset) is not SpeechAsset: raise AudioError('SPEECH_ASSET_REQUIRED')
    info, pcm = validate_wav(asset.wav_bytes, asset.request.settings.format)
    if info != asset.info: raise AudioError('ASSET_METADATA_CHANGED')
    expected_pause = samples_for_ms(asset.request.segment.pause_after_ms, info.sample_rate)
    if expected_pause != asset.requested_pause_samples or expected_pause >= info.samples_per_channel:
        raise AudioError('ASSET_PAUSE_MISMATCH')
    stop = (info.samples_per_channel - expected_pause) * info.channels * 2
    if any(pcm[stop:]) or hashlib.sha256(pcm[:stop]).hexdigest() != asset.provider_pcm_sha256:
        raise AudioError('ASSET_PCM_OR_PAUSE_CHANGED')
    return info, pcm, pcm[:stop]


def validate_alignment(asset: SpeechAsset, aligned: AlignedSpeech, *, require_measured=True):
    info, _, prefix = validate_asset(asset)
    if type(aligned) is not AlignedSpeech: raise AudioError('ALIGNED_SPEECH_REQUIRED')
    r = asset.request; s = r.segment
    expected = (r.fingerprint(), info.sha256, s.fingerprint(), r.voice.runtime_fingerprint,
                info.sample_rate, len(prefix)//(info.channels*2), asset.requested_pause_samples)
    actual = (aligned.request_fingerprint, aligned.media_sha256, aligned.segment_fingerprint,
              aligned.runtime_fingerprint, aligned.sample_rate, aligned.provider_samples, aligned.pause_samples)
    if expected != actual: raise AudioError('STALE_TIMING_BINDING')
    if aligned.basis == 'ELEVENLABS_CHARACTER_EVENTS_SAME_RESPONSE' and r.voice.provider_id != 'elevenlabs-neural-v1':
        raise AudioError('TIMING_PROVIDER_IDENTITY_MISMATCH')
    if aligned.basis == 'NEURAL_CHARACTER_FIXTURE_SAME_PCM':
        from .fixture_scope import synthetic_timing_allowed
        if r.voice.provider_id != 'elevenlabs-contract-fixture-v1':
            raise AudioError('TIMING_PROVIDER_IDENTITY_MISMATCH')
        if require_measured and not synthetic_timing_allowed():
            raise AudioError('SYNTHETIC_TIMING_DIAGNOSTIC_OPT_IN_REQUIRED')
    elif require_measured and aligned.basis not in ('ESPEAK_ENGINE_EVENTS_PCM_REPLAY','ESPEAK_MARK_EVENTS_SAME_PCM',
            'ELEVENLABS_CHARACTER_EVENTS_SAME_RESPONSE'):
        raise AudioError('MEASURED_WORD_TIMING_REQUIRED')
    spoken = s.spoken_text; covered = set()
    for w in aligned.words:
        if spoken[w.spoken_start:w.spoken_end] != w.spoken or source_slices(s,w.spoken_start,w.spoken_end) != w.source:
            raise AudioError('TIMING_SOURCE_CHANGED')
        covered.update(range(w.spoken_start,w.spoken_end))
    if any(significant(ch) and i not in covered for i,ch in enumerate(spoken)):
        raise AudioError('TIMING_WORD_COVERAGE')
    return aligned
