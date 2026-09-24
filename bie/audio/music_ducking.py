"""BIE-AUDIO-MIX-002: linked sample-accurate narration RMS sidechain envelope."""
from dataclasses import dataclass,asdict
import hashlib,numpy as np
from .common import AudioError,fingerprint,integer
from .mix_contract import MixBuffer,number,db_gain
from .sync_contract import samples_for_ms
@dataclass(frozen=True)
class DuckingPolicy:
    reduction_db:float=-15.0
    threshold_dbfs:float=-42.0
    window_ms:int=10
    attack_ms:int=60
    hold_ms:int=160
    release_ms:int=300
    def __post_init__(self):
        number(self.reduction_db,'reduction',-40,-1);number(self.threshold_dbfs,'threshold',-80,-6)
        for k,lo,hi in (('window_ms',1,100),('attack_ms',0,2000),('hold_ms',0,5000),('release_ms',1,5000)):integer(getattr(self,k),k,lo,hi)
@dataclass(frozen=True)
class DuckWindow:
    attack_start:int
    active_start:int
    active_end:int
    release_end:int

def build_duck_envelope(narration,policy=DuckingPolicy()):
    if type(narration)is not MixBuffer or type(policy)is not DuckingPolicy:raise AudioError('DUCKING_INPUT')
    DuckingPolicy(**asdict(policy));rate=narration.sample_rate;n=narration.frames
    step=max(1,samples_for_ms(policy.window_ms,rate));attack=samples_for_ms(policy.attack_ms,rate);hold=samples_for_ms(policy.hold_ms,rate);release=max(1,samples_for_ms(policy.release_ms,rate))
    threshold=db_gain(policy.threshold_dbfs)**2;active=[];a=narration.array()
    for begin in range(0,n,step):
        end=min(n,begin+step)
        if float(np.mean(a[begin:end]**2))>=threshold:
            if active and active[-1][1]==begin:active[-1]=(active[-1][0],end)
            else:active.append((begin,end))
    held=[]
    for start,end in active:
        end=min(n,end+hold)
        if held and start-attack<=held[-1][1]+release:held[-1]=(held[-1][0],max(held[-1][1],end))
        else:held.append((start,end))
    if len(held)>20000:raise AudioError('DUCKING_EVENT_BUDGET')
    depth=db_gain(policy.reduction_db);gain=np.ones(n);windows=[]
    for start,end in held:
        first=max(0,start-attack);last=min(n,end+release)
        if first<start:gain[first:start]=1+(depth-1)*np.arange(start-first)/(start-first)
        gain[start:end]=depth
        if end<last:gain[end:last]=depth+(1-depth)*np.arange(last-end)/(last-end)
        windows.append(DuckWindow(first,start,end,last))
    return gain,tuple(windows)
def duck_music(music,narration,policy=DuckingPolicy()):
    if music.frames!=narration.frames or music.sample_rate!=narration.sample_rate:raise AudioError('DUCKING_CLOCK_MISMATCH')
    envelope,windows=build_duck_envelope(narration,policy);out=MixBuffer.from_array(music.array()*envelope[:,None],music.sample_rate)
    r={'schema_version':'bie.audio.music-duck/1','policy':asdict(policy),'music':music.info(),'sidechain':narration.info(),'output':out.info(),
       'windows':[asdict(x) for x in windows],'envelope_f64le_sha256':hashlib.sha256(envelope.astype('<f8').tobytes()).hexdigest(),
       'time_transform':'IDENTITY','linked_channels':True,'detector':'nonoverlap narration-only RMS; not ASR','product_accepted':False}
    r['fingerprint']=fingerprint(r);return out,r
