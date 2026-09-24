"""BIE-AUDIO-MIX-004: exact-zero edge trim; no internal cuts or inferred breath removal."""
from dataclasses import dataclass,asdict
import numpy as np
from .common import AudioError,fingerprint,integer
from .mix_contract import MixBuffer,SampleSpan,spans
from .sync_contract import samples_for_ms
@dataclass(frozen=True)
class TrimPolicy:
    enabled:bool=True
    padding_ms:int=20
    minimum_silence_ms:int=40
    max_edge_ms:int=2000
    def __post_init__(self):
        if type(self.enabled)is not bool:raise AudioError('TRIM_POLICY')
        for n,lo,hi in (('padding_ms',0,2000),('minimum_silence_ms',0,10000),('max_edge_ms',0,10000)):integer(getattr(self,n),n,lo,hi)
@dataclass(frozen=True)
class TrimPlan:
    input_pcm_fingerprint:str
    sample_rate:int
    input_frames:int
    keep_start:int
    keep_end:int
    protected:tuple[SampleSpan,...]
    policy:TrimPolicy
    def fingerprint(self):return fingerprint(self)
    @property
    def output_frames(self):return self.keep_end-self.keep_start
    def map_sample(self,value):
        integer(value,'source sample',self.keep_start,self.keep_end);return value-self.keep_start

def plan_silence_trim(pcm,policy=TrimPolicy(),protected=()):
    if type(pcm)is not MixBuffer or type(policy)is not TrimPolicy:raise AudioError('TRIM_INPUT')
    TrimPolicy(**asdict(policy));spans(protected,pcm.frames)
    nonzero=np.flatnonzero(np.any(pcm.array()!=0,axis=1))
    if not len(nonzero):raise AudioError('TRIM_NO_SIGNAL')
    first,last=int(nonzero[0]),int(nonzero[-1])+1;start,end=0,pcm.frames
    if policy.enabled:
        pad=samples_for_ms(policy.padding_ms,pcm.sample_rate);minimum=samples_for_ms(policy.minimum_silence_ms,pcm.sample_rate);cap=samples_for_ms(policy.max_edge_ms,pcm.sample_rate)
        if first>=minimum:start=min(cap,max(0,first-pad))
        if pcm.frames-last>=minimum:end=pcm.frames-min(cap,max(0,pcm.frames-last-pad))
        if protected:start=min(start,min(p.start for p in protected));end=max(end,max(p.end for p in protected))
    return TrimPlan(pcm.fingerprint(),pcm.sample_rate,pcm.frames,start,end,protected,policy)
def apply_silence_trim(pcm,plan):
    if type(plan)is not TrimPlan:raise AudioError('TRIM_PLAN_REQUIRED')
    if plan!=plan_silence_trim(pcm,plan.policy,plan.protected):raise AudioError('TRIM_STALE_OR_TAMPERED')
    if np.any(pcm.array()[:plan.keep_start]) or np.any(pcm.array()[plan.keep_end:]):raise AudioError('TRIM_NONZERO_LOSS')
    out=pcm.slice(plan.keep_start,plan.keep_end)
    return out,{'schema_version':'bie.audio.edge-trim/1','plan':asdict(plan),'plan_fingerprint':plan.fingerprint(),'output':out.info(),
                'removed_leading_samples':plan.keep_start,'removed_trailing_samples':plan.input_frames-plan.keep_end,'internal_samples_deleted':0,'acoustic_silence_detection':False,'product_accepted':False}
