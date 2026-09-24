"""BIE-AUDIO-VO-009: actual provider invocation, validation and speech asset receipts."""
from dataclasses import asdict,dataclass
from threading import Event
import hashlib,time
from .common import AudioError,integer
from .tts_contract import SynthesisRequest,SpeechProvider,ProviderAudio,ProviderFailure
from .pcm_audio import PCMInfo,validate_wav,append_requested_pause


@dataclass(frozen=True)
class SpeechAsset:
    request: SynthesisRequest
    wav_bytes: bytes
    info: PCMInfo
    provider_audio_sha256: str
    provider_pcm_sha256: str
    requested_pause_samples: int
    invocation_id: str
    attempts: int
    diagnostics: tuple[str,...]
    def receipt(self):
        return {'schema_version':'bie.audio.speech-asset/1','request_fingerprint':self.request.fingerprint(),
            'request':asdict(self.request),'media':asdict(self.info),'provider_audio_sha256':self.provider_audio_sha256,'provider_pcm_sha256':self.provider_pcm_sha256,
            'requested_pause_samples':self.requested_pause_samples,'invocation_id':self.invocation_id,'attempts':self.attempts,
            'diagnostics':list(self.diagnostics),'audio_generated':True,'word_timestamps_verified':False,
            'pronunciation_verified':False,'cinematic_quality_verified':False,'product_accepted':False}


def generate_speech(request:SynthesisRequest, provider:SpeechProvider, *, cancellation:Event | None=None,
                    max_attempts=2, retry_delay_seconds=.1) -> SpeechAsset:
    if type(request)is not SynthesisRequest or not isinstance(provider,SpeechProvider):raise AudioError('GENERATION_INPUT')
    integer(max_attempts,'attempts',1,4)
    if type(retry_delay_seconds)not in (int,float) or not 0<=retry_delay_seconds<=10:raise AudioError('RETRY_DELAY')
    cancel=cancellation or Event()
    if cancel.is_set():raise ProviderFailure('CANCELLED')
    catalog=provider.catalog()
    if catalog.fingerprint()!=request.catalog_fingerprint or request.voice not in catalog.voices or provider.provider_id!=request.voice.provider_id:
        raise ProviderFailure('PROVIDER_CATALOG_CHANGED')
    for attempt in range(1,max_attempts+1):
        try:result=provider.synthesize(request,cancellation=cancel);break
        except ProviderFailure as exc:
            if not exc.retryable or exc.code=='CANCELLED' or attempt==max_attempts:raise
            if cancel.wait(retry_delay_seconds*attempt):raise ProviderFailure('CANCELLED')
    if cancel.is_set():raise ProviderFailure('CANCELLED')
    if type(result)is not ProviderAudio or result.request_fingerprint!=request.fingerprint() or result.provider_id!=provider.provider_id or result.voice_fingerprint!=request.voice.fingerprint() or result.runtime_fingerprint!=request.voice.runtime_fingerprint:
        raise ProviderFailure('PROVIDER_RECEIPT_MISMATCH')
    if provider.catalog()!=catalog:raise ProviderFailure('PROVIDER_CATALOG_CHANGED')
    before,raw=validate_wav(result.wav_bytes,request.settings.format)
    wav,pause=append_requested_pause(result.wav_bytes,request.settings.format,request.segment.pause_after_ms)
    info,_=validate_wav(wav,request.settings.format)
    return SpeechAsset(request,wav,info,before.sha256,hashlib.sha256(raw).hexdigest(),pause,result.invocation_id,attempt,result.diagnostics)
