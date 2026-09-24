"""Strict bounded PCM WAV validation for VO-009 and cache reads, not acoustic QA."""
from dataclasses import dataclass
import hashlib,io,struct,wave
from .common import AudioError,integer
from .tts_contract import AudioFormat

@dataclass(frozen=True)
class PCMInfo:
    sha256: str
    sample_rate: int
    channels: int
    samples_per_channel: int
    peak: int
    nonzero_samples: int
    bytes: int
    @property
    def duration_seconds(self):return self.samples_per_channel/self.sample_rate


def validate_wav(data, expected:AudioFormat, *, max_bytes=32000000, max_seconds=300):
    if type(data)is not bytes or not 44<=len(data)<=max_bytes:raise AudioError('WAV_SIZE')
    if data[:4]!=b'RIFF' or data[8:12]!=b'WAVE' or struct.unpack_from('<I',data,4)[0]+8!=len(data):raise AudioError('WAV_CONTAINER')
    i=12;chunks={}
    while i<len(data):
        if i+8>len(data):raise AudioError('WAV_CHUNK_TRUNCATED')
        k=data[i:i+4];size=struct.unpack_from('<I',data,i+4)[0];start=i+8;end=start+size
        if end>len(data) or k in chunks:raise AudioError('WAV_CHUNK_INVALID')
        if k not in (b'fmt ',b'data',b'LIST',b'JUNK'):raise AudioError('WAV_CHUNK_UNSUPPORTED')
        chunks[k]=data[start:end];i=end+(size%2)
    if i!=len(data) or set((b'fmt ',b'data'))-set(chunks):raise AudioError('WAV_CHUNKS_MISSING')
    fmt=chunks[b'fmt ']
    if len(fmt) not in (16,18):raise AudioError('WAV_FORMAT')
    tag,ch,rate,byte_rate,block,bits=struct.unpack_from('<HHIIHH',fmt)
    if tag!=1 or bits!=16 or ch!=expected.channels or rate!=expected.sample_rate or block!=ch*2 or byte_rate!=rate*block:raise AudioError('WAV_FORMAT')
    raw=chunks[b'data']
    if not raw or len(raw)%block or len(raw)>int(max_seconds*rate)*block:raise AudioError('WAV_DATA_BOUND')
    peak=count=0
    for (v,) in struct.iter_unpack('<h',raw):peak=max(peak,abs(v));count+=v!=0
    if count==0:raise AudioError('EMPTY_AUDIO_SIGNAL')
    return PCMInfo(hashlib.sha256(data).hexdigest(),rate,ch,len(raw)//block,peak,count,len(data)),raw


def encode_pcm(raw, format:AudioFormat):
    if not raw or len(raw)%(format.channels*2):raise AudioError('PCM_ALIGNMENT')
    b=io.BytesIO()
    with wave.open(b,'wb') as f:
        f.setnchannels(format.channels);f.setsampwidth(2);f.setframerate(format.sample_rate);f.writeframes(raw)
    return b.getvalue()


def append_requested_pause(data, format, milliseconds, *, max_seconds=300):
    integer(milliseconds,'pause',0,3600000)
    info,raw=validate_wav(data,format,max_seconds=max_seconds)
    frames=(milliseconds*format.sample_rate+500)//1000
    if info.samples_per_channel+frames>max_seconds*format.sample_rate:raise AudioError('AUDIO_DURATION_BUDGET')
    combined=encode_pcm(raw+b'\x00'*(frames*format.channels*2),format)
    validate_wav(combined,format,max_seconds=max_seconds)
    return combined,frames
