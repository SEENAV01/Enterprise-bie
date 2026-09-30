"""H2-005: full interleaved float PCM, original channel/rate, bounded windows.

Silence and clipping are numeric diagnostics; activity is NOT speech detection,
word alignment, pronunciation scoring or a listening-quality certification.
"""
from __future__ import annotations
from array import array
import hashlib,math,sys
from ..models import BenchmarkError
from .process import stream,executable
from .probe import input_args

class AudioAccumulator:
    def __init__(self,rate,channels,max_duration_s,window_ms=100):
        from .custody import integer
        integer(rate,1,192000);integer(channels,1,32);integer(max_duration_s,1,7200);integer(window_ms,1,1000)
        self.rate=rate;self.channels=channels;self.window=max(1,rate*window_ms//1000)
        self.stride=self.window*channels*4;self.max_samples=rate*max_duration_s
        self.pending=bytearray();self.samples=0;self.hash=hashlib.sha256();self.window_hash=hashlib.sha256()
        self.peak=[0.0]*channels;self.energy=[0.0]*channels;self.clipped=[0]*channels;self.silent=[0]*channels
        self.activity=[];self.windows=0
    def feed(self,b):
        self.hash.update(b);self.pending.extend(b)
        while len(self.pending)>=self.stride:
            data=bytes(self.pending[:self.stride]);del self.pending[:self.stride];self._window(data)
    def _window(self,data):
        if len(data)%(4*self.channels):raise BenchmarkError('PARTIAL_PCM_SAMPLE')
        a=array('f');a.frombytes(data)
        if sys.byteorder!='little':a.byteswap()
        n=len(a)//self.channels
        if not n:return
        if self.samples+n>self.max_samples:raise BenchmarkError('AUDIO_SAMPLE_LIMIT')
        active=False;stats=[]
        for c in range(self.channels):
            vals=a[c::self.channels]
            if any(not math.isfinite(x) for x in vals):raise BenchmarkError('NONFINITE_PCM_SAMPLE')
            peak=max(abs(x) for x in vals);energy=math.fsum(x*x for x in vals)
            clips=sum(abs(x)>=0.999 for x in vals);rms=math.sqrt(energy/n)
            self.peak[c]=max(self.peak[c],peak);self.energy[c]+=energy;self.clipped[c]+=clips
            if rms<0.001:self.silent[c]+=n
            else:active=True
            stats.append(f'{peak:.12g}:{energy:.12g}:{clips}')
        start=self.samples/self.rate;end=(self.samples+n)/self.rate
        if active:
            if self.activity and abs(self.activity[-1][1]-start)<1e-8:self.activity[-1][1]=end
            else:
                if len(self.activity)>=10000:raise BenchmarkError('AUDIO_ACTIVITY_FRAGMENT_LIMIT')
                self.activity.append([start,end])
        self.samples+=n;self.windows+=1
        self.window_hash.update(('|'.join(stats)+'\n').encode())
    def finish(self):
        if self.pending:self._window(bytes(self.pending));self.pending.clear()
        if not self.samples:raise BenchmarkError('NO_DECODED_AUDIO')
        return {'samples_per_channel':self.samples,'rate':self.rate,'channels':self.channels,
                'duration_s':self.samples/self.rate,'peak_per_channel':self.peak,
                'rms_per_channel':[math.sqrt(e/self.samples) for e in self.energy],
                'clipped_samples_per_channel':self.clipped,'silent_samples_per_channel':self.silent,
                'windows':self.windows,'activity_intervals_relative_s':self.activity,
                'window_size_samples':self.window,'activity_is_speech_recognition':False,
                'decoded_sha256':self.hash.hexdigest(),'window_stats_sha256':self.window_hash.hexdigest()}

def decode_audio(path,metadata,limits,deadline):
    a=metadata['audio']
    if a is None: return None,None
    acc=AudioAccumulator(a['rate'],a['channels'],limits.max_duration_s)
    argv=[executable('ffmpeg'),'-nostdin','-v','error','-xerror','-threads','1',*input_args(path),
          '-map',f"0:{a['index']}",'-vn','-sn','-dn','-threads','1','-c:a','pcm_f32le','-f','f32le','pipe:1']
    cmd=stream(argv,path.parent,deadline,acc.feed,max_stdout=min(limits.max_decoded_bytes,acc.max_samples*a['channels']*4+4*a['channels']),max_stderr=limits.max_stderr_bytes)
    result=acc.finish()
    if cmd['stdout_bytes']!=result['samples_per_channel']*a['channels']*4:raise BenchmarkError('AUDIO_BYTE_COUNT_MISMATCH')
    return result,cmd
