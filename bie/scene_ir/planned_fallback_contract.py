from dataclasses import dataclass
from .capability_common import *

@dataclass(frozen=True)
class PlannedFallback:
    fallback_id:str;element_id:str;missing_capability_id:str;fallback_capability_id:str;fallback_action:str
    semantic_equivalence:str;preserves_source_refs:bool;preserves_reasoning_refs:bool;preserves_accessibility:bool
    required_review:bool=True
    def __post_init__(self):
        for f in ('fallback_id','element_id','missing_capability_id','fallback_capability_id','fallback_action'): object.__setattr__(self,f,tok(getattr(self,f),f))
        if self.semantic_equivalence not in {'equivalent','degraded_but_safe','illustrative_only'}: raise SceneIRCapabilityError('bad semantic_equivalence')

def validate_fallback(f,registry,target_profile,element_type):
    blockers=[]; warnings=[]
    if not registry.supports(f.fallback_capability_id,element_type=element_type,profile=target_profile): blockers.append('fallback_capability_unsupported')
    if not f.preserves_source_refs: blockers.append('fallback_loses_source_refs')
    if not f.preserves_reasoning_refs: blockers.append('fallback_loses_reasoning_refs')
    if not f.preserves_accessibility: blockers.append('fallback_loses_accessibility')
    if f.semantic_equivalence=='illustrative_only': warnings.append('fallback_is_illustrative_only')
    return tuple(sorted(blockers)),tuple(sorted(warnings))

def apply_fallback_or_fail(f,registry,target_profile,element_type):
    blockers,warnings=validate_fallback(f,registry,target_profile,element_type)
    if blockers: raise SceneIRCapabilityError('invalid planned fallback')
    return {'element_id':f.element_id,'fallback_capability_id':f.fallback_capability_id,'fallback_action':f.fallback_action,'semantic_equivalence':f.semantic_equivalence,'warnings':warnings,'accepted':False}
