"""Strict bounded RIFF PCM16 reader. Actual samples, not reported durations."""
from dataclasses import dataclass
from fractions import Fraction
from array import array
import sys,struct
from ..release_v2.contracts import ContractError

@dataclass(frozen=True,slots=True)
class PCM:
    sample_rate:int
    channels:int
    samples:int
    data:bytes
    @property
    def duration_ms(self):return Fraction(1000*self.samples,self.sample_rate)
    def amplitudes(self):
        a=array('h');a.frombytes(self.data)
        if sys.byteorder!='little':a.byteswap()
        return a
    def stats(self):
        a=self.amplitudes();return dict(peak=max(abs(x) for x in a),clipped=sum(x<=-32768 or x>=32767 for x in a),values=len(a),nonzero=sum(x!=0 for x in a))
    def has_signal(self,start,end):
        if not 0<=start<end<=self.samples:raise ContractError('AUDIO_SAMPLE_RANGE')
        return any(self.data[start*self.channels*2:end*self.channels*2])

def read_pcm(data):
    if type(data) is not bytes or not 44<=len(data)<=16*1024*1024:raise ContractError('AUDIO_WAV_SIZE')
    if data[:4]!=b'RIFF' or data[8:12]!=b'WAVE' or struct.unpack_from('<I',data,4)[0]!=len(data)-8:raise ContractError('AUDIO_RIFF_HEADER_OR_SIZE')
    chunks={};offset=12
    while offset<len(data):
        if offset+8>len(data):raise ContractError('AUDIO_CHUNK_HEADER')
        name=data[offset:offset+4];size=struct.unpack_from('<I',data,offset+4)[0];a=offset+8;b=a+size
        if b+(size%2)>len(data):raise ContractError('AUDIO_TRUNCATED_CHUNK')
        if name in chunks:raise ContractError('AUDIO_DUPLICATE_CHUNK')
        if name not in (b'fmt ',b'data',b'LIST',b'JUNK',b'fact'):raise ContractError('AUDIO_UNSUPPORTED_CHUNK')
        chunks[name]=data[a:b];offset=b+size%2
    fmt=chunks.get(b'fmt ',b'');pcm=chunks.get(b'data',b'')
    if len(fmt)!=16 or not pcm:raise ContractError('AUDIO_PCM_FORMAT_OR_EMPTY')
    tag,channels,rate,byte_rate,align,bits=struct.unpack('<HHIIHH',fmt)
    if tag!=1 or bits!=16 or channels not in (1,2) or not 8000<=rate<=192000:raise ContractError('AUDIO_UNSUPPORTED_PCM_FORMAT')
    if align!=channels*2 or byte_rate!=rate*align or len(pcm)%align:raise ContractError('AUDIO_PCM_ALIGNMENT')
    samples=len(pcm)//align
    if samples>rate*600:raise ContractError('AUDIO_DURATION_LIMIT')
    return PCM(rate,channels,samples,pcm)
