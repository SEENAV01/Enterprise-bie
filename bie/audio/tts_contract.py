"""BIE-AUDIO-VO-007: provider-neutral, immutable, source-bound synthesis contracts.

Capabilities are negotiated before execution. Unknown features cannot be silently
ignored. A successful waveform is not pronunciation or educational acceptance.
"""
from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from threading import Event
from .common import AudioError,digest,fingerprint,integer,locale,refs,text
from .speech_contract import SpeechSegment,records


@dataclass(frozen=True)
class AudioFormat:
    sample_rate: int = 22050
    channels: int = 1
    sample_width: int = 2
    encoding: str = 'wav-pcm-s16le'
    def __post_init__(self):
        integer(self.sample_rate,'sample rate',8000,192000)
        if self.channels not in (1,2) or type(self.channels)is not int or self.sample_width!=2 or type(self.sample_width)is not int or self.encoding!='wav-pcm-s16le':
            raise AudioError('UNSUPPORTED_AUDIO_FORMAT')


@dataclass(frozen=True)
class LocaleBinding:
    language: str
    engine_voice: str
    def __post_init__(self):locale(self.language);text(self.engine_voice,'engine voice',128)


@dataclass(frozen=True)
class Voice:
    voice_id: str
    provider_id: str
    model_revision: str
    runtime_fingerprint: str
    primary_language: str
    locales: tuple[LocaleBinding,...]
    formats: tuple[AudioFormat,...]
    features: tuple[str,...]
    quality_class: str
    evidence_refs: tuple[str,...]
    max_chars: int = 20000
    max_utf8_bytes: int = 80000
    same_voice_code_switching: bool = False
    def __post_init__(self):
        for n in ('voice_id','provider_id','model_revision','quality_class'):text(getattr(self,n),n,1024)
        digest(self.runtime_fingerprint);locale(self.primary_language)
        records(self.locales,LocaleBinding,'voice locales');records(self.formats,AudioFormat,'formats')
        refs(self.features,'features',False);refs(self.evidence_refs,'voice provenance')
        if len({x.language for x in self.locales})!=len(self.locales) or self.primary_language not in {x.language for x in self.locales}:raise AudioError('VOICE_LANGUAGE_BINDINGS')
        integer(self.max_chars,'voice chars',1,1000000);integer(self.max_utf8_bytes,'voice bytes',1,8000000)
        if type(self.same_voice_code_switching)is not bool:raise AudioError('VOICE_POLICY_BOOLEAN')
    def fingerprint(self):return fingerprint(self)


@dataclass(frozen=True)
class VoiceCatalog:
    revision: str
    voices: tuple[Voice,...]
    def __post_init__(self):
        text(self.revision,'catalog revision',1024);records(self.voices,Voice,'catalog voices')
        if len({(v.provider_id,v.voice_id) for v in self.voices})!=len(self.voices):raise AudioError('DUPLICATE_VOICE')
        if self.voices!=tuple(sorted(self.voices,key=lambda v:(v.provider_id,v.voice_id))):raise AudioError('UNORDERED_CATALOG')
    def fingerprint(self):return fingerprint(self)


@dataclass(frozen=True)
class SynthesisSettings:
    format: AudioFormat = AudioFormat()
    rate_wpm: int = 155
    pitch: int = 50
    amplitude: int = 80
    style: str = 'neutral'
    def __post_init__(self):
        if type(self.format)is not AudioFormat:raise AudioError('AUDIO_FORMAT_REQUIRED')
        integer(self.rate_wpm,'rate',80,300);integer(self.pitch,'pitch',0,99);integer(self.amplitude,'amplitude',1,100)
        text(self.style,'style',64)


@dataclass(frozen=True)
class SynthesisRequest:
    plan_fingerprint: str
    segment: SpeechSegment
    voice: Voice
    catalog_fingerprint: str
    selection_fingerprint: str
    settings: SynthesisSettings
    version: str = 'bie.audio.tts-request/1'
    def __post_init__(self):
        if self.version!='bie.audio.tts-request/1':raise AudioError('REQUEST_VERSION')
        for value in (self.plan_fingerprint,self.catalog_fingerprint,self.selection_fingerprint):digest(value)
        if type(self.segment)is not SpeechSegment or type(self.voice)is not Voice or type(self.settings)is not SynthesisSettings:raise AudioError('TYPED_TTS_REQUEST_REQUIRED')
        if self.settings.format not in self.voice.formats:raise AudioError('VOICE_FORMAT_UNSUPPORTED')
        if self.settings.style!='neutral' and 'style:'+self.settings.style not in self.voice.features:raise AudioError('VOICE_STYLE_UNSUPPORTED')
        if not set(self.segment.languages)<={x.language for x in self.voice.locales}:raise AudioError('VOICE_LOCALE_UNSUPPORTED')
        if any(s.phonemes is not None for s in self.segment.spans) and 'phoneme:ipa' not in self.voice.features:raise AudioError('VOICE_PHONEMES_UNSUPPORTED')
        if len(self.segment.languages)>1 and 'language-switch' not in self.voice.features:raise AudioError('VOICE_CODE_SWITCH_UNSUPPORTED')
        if len(self.segment.spoken_text)>self.voice.max_chars or len(self.segment.spoken_text.encode())>self.voice.max_utf8_bytes:raise AudioError('VOICE_REQUEST_LIMIT')
    def fingerprint(self):return fingerprint(self)


@dataclass(frozen=True)
class ProviderAudio:
    request_fingerprint: str
    provider_id: str
    voice_fingerprint: str
    runtime_fingerprint: str
    wav_bytes: bytes
    invocation_id: str
    diagnostics: tuple[str,...] = ()
    def __post_init__(self):
        for d in (self.request_fingerprint,self.voice_fingerprint,self.runtime_fingerprint):digest(d)
        text(self.provider_id,'provider',256);text(self.invocation_id,'invocation',1024)
        refs(self.diagnostics,'diagnostics',False)
        if type(self.wav_bytes)is not bytes or not self.wav_bytes or len(self.wav_bytes)>100000000:raise AudioError('PROVIDER_MEDIA_BUDGET')


class ProviderFailure(AudioError):
    def __init__(self, code, detail='', *, retryable=False):
        super().__init__(code,detail)
        if type(retryable)is not bool:raise AudioError('INVALID_RETRY_CLASS')
        self.retryable=retryable


@runtime_checkable
class SpeechProvider(Protocol):
    provider_id: str
    def catalog(self) -> VoiceCatalog: ...
    def synthesize(self, request: SynthesisRequest, *, cancellation: Event | None = None) -> ProviderAudio: ...
