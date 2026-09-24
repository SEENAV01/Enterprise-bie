"""H1-003: byte-bound provider timing; no independently verified acoustic claim.

Raw signed-16 PCM is wrapped losslessly in WAV. Character timings must cover the
EXACT prepared text; normalized text cannot silently replace source readings.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import base64, hashlib, json, re, math
from .common import AudioError, fingerprint, strict_json, boundary
from .tts_contract import ProviderAudio
from .pcm_audio import encode_pcm, validate_wav
from .sync_contract import AlignedSpeech, WordStamp, source_slices, validate_alignment


@dataclass(frozen=True)
class DecodedNeural:
    wav_bytes: bytes
    character_starts: tuple[int,...]
    character_ends: tuple[int,...]
    response_sha256: str
    samples: int


def _sample(value,rate,limit):
    if type(value) not in (int,float) or not math.isfinite(value) or value<0:
        raise AudioError('NEURAL_TIMESTAMP_NONFINITE')
    n=int((Decimal(str(value))*rate).quantize(Decimal(1),rounding=ROUND_HALF_UP))
    if not 0<=n<=limit: raise AudioError('NEURAL_TIMESTAMP_AUDIO_BOUNDS')
    return n


def decode_response(reply,request,*,max_bytes):
    if type(reply.body)is not bytes or len(reply.body)>max_bytes:
        raise AudioError('NEURAL_RESPONSE_BUDGET')
    try: row=strict_json(reply.body.decode('utf-8'))
    except (UnicodeError,ValueError): raise AudioError('NEURAL_RESPONSE_JSON') from None
    if type(row)is not dict or set(row)!= {'audio_base64','alignment','normalized_alignment'}:
        raise AudioError('NEURAL_RESPONSE_SCHEMA')
    encoded=row['audio_base64']
    if type(encoded)is not str or len(encoded)>max_bytes: raise AudioError('NEURAL_AUDIO_ENCODING')
    try: raw=base64.b64decode(encoded,validate=True)
    except (ValueError,TypeError): raise AudioError('NEURAL_AUDIO_ENCODING') from None
    fmt=request.settings.format
    if fmt.channels!=1 or len(raw)%2 or not raw or len(raw)>fmt.sample_rate*2*300:
        raise AudioError('NEURAL_PCM_LAYOUT')
    wav=encode_pcm(raw,fmt); info,_=validate_wav(wav,fmt)
    spoken=request.segment.spoken_text; timing=row['alignment']
    starts=ends=None
    for name in ('alignment','normalized_alignment'):
        a=row[name]
        if name=='normalized_alignment' and a is None: continue
        if type(a)is not dict or set(a)!={'characters','character_start_times_seconds','character_end_times_seconds'}:
            raise AudioError('NEURAL_ALIGNMENT_MISSING_OR_SCHEMA')
        chars=a['characters'];ss=a['character_start_times_seconds'];ee=a['character_end_times_seconds']
        if type(chars)is not list or type(ss)is not list or type(ee)is not list or not len(chars)==len(ss)==len(ee)==len(spoken):
            raise AudioError('NEURAL_CHARACTER_COUNT')
        if any(type(c)is not str or len(c)!=1 for c in chars) or ''.join(chars)!=spoken:
            raise AudioError('NEURAL_TEXT_NORMALIZED_OR_CHANGED')
        s=tuple(_sample(v,fmt.sample_rate,info.samples_per_channel) for v in ss)
        e=tuple(_sample(v,fmt.sample_rate,info.samples_per_channel) for v in ee)
        if any(x>y for x,y in zip(s,e)) or any(a>b for a,b in zip(s,s[1:])) or any(a>b for a,b in zip(e,e[1:])):
            raise AudioError('NEURAL_CHARACTER_TIME_ORDER')
        if name=='alignment': starts,ends=s,e
    previous_end=0
    for m in re.finditer(r'\S+',spoken):
        a,b=m.span()
        if ends[b-1]<=starts[a]: raise AudioError('WORD_TIME_RANGE')
        if starts[a]<previous_end: raise AudioError('NEURAL_WORD_TIME_OVERLAP')
        previous_end=ends[b-1]
    return DecodedNeural(wav,starts,ends,hashlib.sha256(reply.body).hexdigest(),info.samples_per_channel)


def bind_neural_alignment(asset,decoded,*,producer_fingerprint,request_id,fixture=False):
    if hashlib.sha256(decoded.wav_bytes).hexdigest()!=asset.provider_audio_sha256:
        raise AudioError('NEURAL_TIMING_WAVEFORM_MISMATCH')
    _,raw=validate_wav(decoded.wav_bytes,asset.request.settings.format)
    if hashlib.sha256(raw).hexdigest()!=asset.provider_pcm_sha256:
        raise AudioError('NEURAL_TIMING_PCM_MISMATCH')
    s=asset.request.segment; spoken=s.spoken_text; words=[]
    for m in re.finditer(r'\S+',spoken):
        a,b=m.span()
        if not boundary(spoken,a) or not boundary(spoken,b): raise AudioError('NEURAL_WORD_CLUSTER')
        words.append(WordStamp(len(words),a,b,m.group(),decoded.character_starts[a],decoded.character_ends[b-1],
                               source_slices(s,a,b),'REPORTED_INTERVAL'))
    event=fingerprint({'response_sha256':decoded.response_sha256,'request_id':request_id,
                       'request':asset.request.fingerprint(),'fixture':fixture})
    basis='NEURAL_CHARACTER_FIXTURE_SAME_PCM' if fixture else 'ELEVENLABS_CHARACTER_EVENTS_SAME_RESPONSE'
    out=AlignedSpeech(asset.request.fingerprint(),asset.info.sha256,s.fingerprint(),asset.request.voice.runtime_fingerprint,
        producer_fingerprint,event,asset.info.sample_rate,decoded.samples,asset.requested_pause_samples,tuple(words),basis)
    validate_alignment(asset,out)
    return out
