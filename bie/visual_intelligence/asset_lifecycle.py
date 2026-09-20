from dataclasses import dataclass,field,replace
import re
class AssetLifecycleError(ValueError): pass
class AssetTransitionError(AssetLifecycleError): pass
HEX64=re.compile(r'^[0-9a-f]{64}$')
STATES=('NEEDED','REUSE_CANDIDATE','GENERATION_REQUESTED','EXTERNAL_REQUESTED','ACQUIRED','GROUNDING_CHECKED','RIGHTS_VERIFIED','QUALITY_VERIFIED','READY','FALLBACK','BLOCKED')
ALLOWED={'NEEDED':{'REUSE_CANDIDATE','GENERATION_REQUESTED','EXTERNAL_REQUESTED','FALLBACK','BLOCKED'},'REUSE_CANDIDATE':{'ACQUIRED','FALLBACK','BLOCKED'},'GENERATION_REQUESTED':{'ACQUIRED','FALLBACK','BLOCKED'},'EXTERNAL_REQUESTED':{'ACQUIRED','FALLBACK','BLOCKED'},'ACQUIRED':{'GROUNDING_CHECKED','BLOCKED'},'GROUNDING_CHECKED':{'RIGHTS_VERIFIED','BLOCKED'},'RIGHTS_VERIFIED':{'QUALITY_VERIFIED','BLOCKED'},'QUALITY_VERIFIED':{'READY','FALLBACK','BLOCKED'},'FALLBACK':{'ACQUIRED','BLOCKED'},'READY':set(),'BLOCKED':set()}
@dataclass(frozen=True)
class AssetLifecycle:
    asset_id:str; state:str='NEEDED'; source_kind:str|None=None; uri:str|None=None; content_sha256:str|None=None; provenance_refs:tuple[str,...]=(); grounding_score:float|None=None; rights_status:str|None=None; attribution:str|None=None; quality_score:float|None=None; history:tuple[tuple[str,str],...]=(); metadata:dict=field(default_factory=dict)
    def __post_init__(self):
        if not self.asset_id or self.state not in STATES: raise AssetLifecycleError('invalid asset/state')
        if self.content_sha256 is not None and not HEX64.fullmatch(self.content_sha256): raise AssetLifecycleError('invalid hash')
        for s in (self.grounding_score,self.quality_score):
            if s is not None and not 0<=float(s)<=1: raise AssetLifecycleError('invalid score')
def transition(asset,new_state,reason,**updates):
    if new_state not in STATES or new_state not in ALLOWED[asset.state]: raise AssetTransitionError(f'illegal transition {asset.state}->{new_state}')
    if not reason: raise AssetTransitionError('reason required')
    nxt=replace(asset,state=new_state,history=asset.history+((new_state,reason),),**updates)
    if new_state=='ACQUIRED' and (not nxt.uri or not nxt.content_sha256 or not nxt.provenance_refs): raise AssetTransitionError('ACQUIRED requires uri/hash/provenance')
    if new_state=='GROUNDING_CHECKED' and (nxt.grounding_score is None or nxt.grounding_score<.70): raise AssetTransitionError('grounding floor failed')
    if new_state=='RIGHTS_VERIFIED' and nxt.rights_status not in {'owned','public_domain','licensed','source-permitted'}: raise AssetTransitionError('rights not usable')
    if new_state=='QUALITY_VERIFIED' and (nxt.quality_score is None or nxt.quality_score<.65): raise AssetTransitionError('quality floor failed')
    if new_state=='READY' and (not nxt.uri or not nxt.content_sha256 or nxt.grounding_score is None or nxt.rights_status is None or nxt.quality_score is None): raise AssetTransitionError('READY missing evidence')
    return nxt
def production_ready(a): return a.state=='READY' and a.uri is not None and a.content_sha256 is not None and a.rights_status in {'owned','public_domain','licensed','source-permitted'}
