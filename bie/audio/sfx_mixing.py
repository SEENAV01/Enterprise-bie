"""BIE-AUDIO-MIX-003: actual explicit sample-domain stems; no implicit resampling."""
from dataclasses import dataclass,asdict
import math,numpy as np
from .common import AudioError,integer,refs,text
from .mix_contract import MixBuffer,SampleSpan,spans,number,db_gain
from .tts_contract import AudioFormat
@dataclass(frozen=True)
class Stem:
    asset_id:str
    role:str
    pcm:MixBuffer
    start_sample:int
    trim_start:int
    trim_end:int
    source_refs:tuple[str,...]
    rights_ref:str
    gain_db:float=0.0
    channel_map:str='identity'
    pan:float=0.0
    repeat:int=1
    fade_in_samples:int=0
    fade_out_samples:int=0
    def __post_init__(self):
        text(self.asset_id,'asset',2048);text(self.rights_ref,'rights',4096);refs(self.source_refs,'sources')
        if self.role not in ('music','sfx') or type(self.pcm)is not MixBuffer:raise AudioError('MIX_STEM_ROLE')
        integer(self.start_sample,'start',0,192000*1800);integer(self.trim_start,'trim start',0,self.pcm.frames);integer(self.trim_end,'trim end',self.trim_start+1,self.pcm.frames)
        integer(self.repeat,'repeat',1,1024);number(self.gain_db,'gain',-96,24);number(self.pan,'pan',-1,1)
        if self.channel_map not in ('identity','mono_dual','mono_equal_power'):raise AudioError('MIX_CHANNEL_MAP')
        if self.channel_map!='mono_equal_power' and self.pan!=0:raise AudioError('MIX_UNUSED_PAN')
        for name in ('fade_in_samples','fade_out_samples'):integer(getattr(self,name),name,0,self.length)
        if self.fade_in_samples+self.fade_out_samples>self.length:raise AudioError('MIX_FADES_OVERLAP')
    @property
    def length(self):return (self.trim_end-self.trim_start)*self.repeat
    def metadata(self):return {**{k:v for k,v in self.__dict__.items() if k!='pcm'},'pcm':self.pcm.info()}

def place_stems(stems,*,rate,channels,frames,role,protected_silence=()):
    if type(stems)is not tuple or len(stems)>128 or any(type(s)is not Stem for s in stems):raise AudioError('MIX_STEMS')
    if len({s.asset_id for s in stems})!=len(stems):raise AudioError('MIX_DUPLICATE_ASSET_ID')
    AudioFormat(rate,channels)
    if role not in ('music','sfx'):raise AudioError('MIX_BUS_ROLE')
    integer(frames,'frames',1,rate*1800)
    if frames*channels*2>64_000_000:raise AudioError('MIX_JOB_BUDGET')
    spans(protected_silence,frames);total=np.zeros((frames,channels));rows=[]
    for s in sorted(stems,key=lambda x:x.asset_id):
        Stem(**s.__dict__)
        if s.role!=role:continue
        if s.pcm.sample_rate!=rate:raise AudioError('MIX_RATE_MISMATCH')
        a,b=s.start_sample,s.start_sample+s.length
        if b>frames:raise AudioError('MIX_EXTENSION_REQUIRED',s.asset_id)
        if role=='sfx' and any(a<p.end and p.start<b for p in protected_silence):raise AudioError('SFX_OVER_REQUIRED_SILENCE')
        values=s.pcm.array()[s.trim_start:s.trim_end]
        if s.channel_map=='identity':
            if s.pcm.channels!=channels:raise AudioError('MIX_CHANNEL_MISMATCH')
        else:
            if s.pcm.channels!=1 or channels!=2:raise AudioError('MIX_CHANNEL_MAP_INVALID')
            if s.channel_map=='mono_dual':values=np.repeat(values,2,axis=1)
            else:
                angle=(s.pan+1)*math.pi/4;values=values*np.array([math.cos(angle),math.sin(angle)])[None,:]
        values=np.tile(values,(s.repeat,1))*db_gain(s.gain_db)
        fi,fo=s.fade_in_samples,s.fade_out_samples
        if fi:values[:fi]*=(np.arange(fi)/fi)[:,None]
        if fo:values[-fo:]*=(np.arange(fo-1,-1,-1)/fo)[:,None]
        total[a:b]+=values;rows.append({**s.metadata(),'output_start':a,'output_end':b})
    out=MixBuffer.from_array(total,rate)
    return out,{'role':role,'stems':rows,'float_sum':out.info(),'sample_rate_conversion':False,'sorting':'asset_id stable float64 accumulation','product_accepted':False}

def silence_music_windows(music,windows,*,fade_samples=0):
    spans(windows,music.frames,nonoverlap=True);integer(fade_samples,'pause fade',0,music.sample_rate*2)
    env=np.ones(music.frames)
    for p in windows:
        a,b=p.start,p.end;left=max(0,a-fade_samples);right=min(music.frames,b+fade_samples)
        if left<a:env[left:a]=np.minimum(env[left:a],np.arange(a-left,0,-1)/(a-left))
        env[a:b]=0
        if b<right:env[b:right]=np.minimum(env[b:right],np.arange(right-b)/(right-b))
    out=MixBuffer.from_array(music.array()*env[:,None],music.sample_rate)
    return out,{'policy':'ALL_STEMS_SILENT','pause_fade_samples':fade_samples,'windows':[asdict(w) for w in windows],'input':music.info(),'output':out.info()}

def sum_buses(narration,music,sfx):
    if any((b.sample_rate,b.channels,b.frames)!=(narration.sample_rate,narration.channels,narration.frames) for b in (music,sfx)):raise AudioError('MIX_BUS_CLOCK_MISMATCH')
    return MixBuffer.from_array(narration.array()+music.array()+sfx.array(),narration.sample_rate)
