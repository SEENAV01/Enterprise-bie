"""AUDIO MIX shared sample-domain contracts. Float headroom is never hard-clipped."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,io,math,wave
import numpy as np
from .common import AudioError,fingerprint,integer,refs,text
from .pcm_audio import validate_wav,encode_pcm
from .tts_contract import AudioFormat
MAX_PCM_BYTES=64_000_000
MAX_SECONDS=1800

def number(value,name,low,high):
    if type(value) not in (int,float) or not math.isfinite(value) or not low<=value<=high:
        raise AudioError('MIX_NUMBER',name)
    return float(value)
def db_gain(db):return 10**(number(db,'gain',-120,36)/20)
def dbfs(value):return None if value==0 else 20*math.log10(abs(value))
def hash64(value):
    if type(value)is not str or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):raise AudioError('MIX_HASH')
    return value

@dataclass(frozen=True)
class MixBuffer:
    sample_rate:int
    channels:int
    f64le:bytes
    def __post_init__(self):
        AudioFormat(self.sample_rate,self.channels)
        if type(self.f64le)is not bytes or not self.f64le or len(self.f64le)%(8*self.channels):raise AudioError('MIX_PCM_SHAPE')
        if len(self.f64le)>MAX_PCM_BYTES*4 or self.frames>self.sample_rate*MAX_SECONDS:raise AudioError('MIX_JOB_BUDGET')
        if not np.isfinite(self.array()).all() or self.sample_peak>256:raise AudioError('MIX_NONFINITE_OR_HEADROOM')
    @property
    def frames(self):return len(self.f64le)//(8*self.channels)
    @property
    def sha256(self):return hashlib.sha256(self.f64le).hexdigest()
    @property
    def sample_peak(self):return float(np.max(np.abs(self.array())))
    def array(self):return np.frombuffer(self.f64le,dtype='<f8').reshape(-1,self.channels)
    def fingerprint(self):return fingerprint({'rate':self.sample_rate,'channels':self.channels,'frames':self.frames,'pcm_sha256':self.sha256})
    def info(self):return {'sample_rate':self.sample_rate,'channels':self.channels,'frames':self.frames,'f64le_sha256':self.sha256,'sample_peak_dbfs':dbfs(self.sample_peak)}
    @classmethod
    def from_array(cls,values,rate):
        a=np.asarray(values)
        if a.dtype.kind not in 'fiu' or a.ndim!=2 or a.shape[1] not in (1,2):raise AudioError('MIX_ARRAY_SHAPE')
        AudioFormat(rate,a.shape[1])
        if a.size>MAX_PCM_BYTES//2 or a.shape[0]>rate*MAX_SECONDS:raise AudioError('MIX_JOB_BUDGET')
        return cls(rate,a.shape[1],a.astype('<f8').tobytes())
    @classmethod
    def from_wav(cls,data,expected):
        if type(expected)is not AudioFormat:raise AudioError('MIX_FORMAT_REQUIRED')
        try:_,raw=validate_wav(data,expected,max_bytes=MAX_PCM_BYTES+1024,max_seconds=MAX_SECONDS)
        except AudioError as e:
            if e.code!='EMPTY_AUDIO_SIGNAL':raise
            # The inherited parser validates all RIFF/format/size fields BEFORE this exception.
            with wave.open(io.BytesIO(data),'rb') as w:raw=w.readframes(w.getnframes())
        return cls.from_array(np.frombuffer(raw,dtype='<i2').reshape(-1,expected.channels).astype(np.float64)/32768,expected.sample_rate)
    def to_wav(self):
        quantized=np.rint(self.array()*32768)
        if quantized.min()<-32768 or quantized.max()>32767:raise AudioError('MIX_ENCODING_WOULD_CLIP')
        return encode_pcm(quantized.astype('<i2').tobytes(),AudioFormat(self.sample_rate,self.channels))
    def gain(self,db):return MixBuffer.from_array(self.array()*db_gain(db),self.sample_rate)
    def slice(self,start,end):
        integer(start,'slice start',0,self.frames);integer(end,'slice end',start+1,self.frames)
        return MixBuffer.from_array(self.array()[start:end],self.sample_rate)

@dataclass(frozen=True)
class SampleSpan:
    start:int
    end:int
    owner:str
    source_refs:tuple[str,...]
    def __post_init__(self):
        integer(self.start,'span start',0,192000*1800);integer(self.end,'span end',self.start+1,192000*1800)
        text(self.owner,'span owner',2048);refs(self.source_refs,'span source')
def spans(values,frames,*,nonoverlap=False):
    if type(values)is not tuple or len(values)>200000 or any(type(x)is not SampleSpan for x in values):raise AudioError('MIX_SPANS')
    for x in values:
        SampleSpan(**x.__dict__)
        if x.end>frames:raise AudioError('MIX_SPAN_OUTSIDE')
    seq=sorted(values,key=lambda x:(x.start,x.end))
    if nonoverlap and any(a.end>b.start for a,b in zip(seq,seq[1:])):raise AudioError('MIX_SPANS_OVERLAP')
    return values
