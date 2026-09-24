"""QA-002: remeasure delivered PCM rather than trust a saved PASS/peak number."""
from dataclasses import asdict,dataclass
import numpy as np
from .common import AudioError,integer
from .mix_contract import MixBuffer,number
from .mix_meter import FFmpegMeter
from .qa_contract import Finding,check,TASKS

@dataclass(frozen=True)
class ClippingPolicy:
    ceiling_dbtp:float=-1.0
    rail_run_samples:int=3
    def __post_init__(self):
        number(self.ceiling_dbtp,'ceiling',-20,0);integer(self.rail_run_samples,'rail run',2,1024)

def longest_run(mask):
    if not np.any(mask):return 0
    edges=np.diff(np.r_[False,mask,False].astype(np.int8));a=np.where(edges==1)[0];b=np.where(edges==-1)[0]
    return int(np.max(b-a))

def clipping_qa(wav,fmt,policy=ClippingPolicy(),*,meter=None,cancellation=None):
    if type(policy)is not ClippingPolicy:raise AudioError('QA_CLIPPING_POLICY')
    ClippingPolicy(**asdict(policy));pcm=MixBuffer.from_wav(wav,fmt);a=np.rint(pcm.array()*32768).astype(np.int32)
    channels=[];fs=[]
    for i in range(pcm.channels):
        x=a[:,i];pos=x==32767;neg=x==-32768;run=max(longest_run(pos),longest_run(neg));count=int(np.count_nonzero(pos|neg))
        channels.append({'channel':i,'rail_contacts':count,'longest_same_rail_run':run})
        if count:fs.append(Finding('PCM_RAIL_RUN' if run>=policy.rail_run_samples else 'PCM_RAIL_CONTACT',
            'FAIL' if run>=policy.rail_run_samples else 'REVIEW','AUDIO/MIX',f'channel/{i}',
            'Rail samples are measured; prior analog clipping below the rails is not proven or excluded.'))
    native=meter or FFmpegMeter()
    measured=native.measure(pcm,cancellation=cancellation)
    if measured.pcm_fingerprint!=pcm.fingerprint() or (measured.frames,measured.sample_rate,measured.channels)!=(pcm.frames,pcm.sample_rate,pcm.channels):raise AudioError('QA_METER_BINDING')
    peak=measured.true_peak_dbtp
    if peak is None:fs.append(Finding('SILENT_OR_UNMEASURABLE_SIGNAL','FAIL','AUDIO/MIX','master.wav','No nonzero programme true peak was measured.'))
    elif peak>policy.ceiling_dbtp:fs.append(Finding('TRUE_PEAK_CEILING_EXCEEDED','FAIL','AUDIO/MIX','master.wav','Fresh measured true peak exceeds the explicit ceiling.'))
    return check(TASKS[1],'Digital PCM rails and fresh FFmpeg true-peak measurement',fs,
        {'channels':channels,'measurement':asdict(measured),'policy':asdict(policy),'meter_identity':native.identity,
         'formal_meter_certification':False,'prior_analog_clipping_excluded':False})
