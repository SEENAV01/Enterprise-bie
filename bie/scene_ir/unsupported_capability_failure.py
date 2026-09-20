from dataclasses import dataclass
from .capability_common import *

@dataclass(frozen=True)
class CapabilityRequest:
    capability_id:str;element_id:str;element_type:str;requested_action:str;target_profile:str;reason_code:str;required:bool=True
    def __post_init__(self):
        for f in ('capability_id','element_id','element_type','requested_action','target_profile','reason_code'): object.__setattr__(self,f,tok(getattr(self,f),f))

@dataclass(frozen=True)
class CapabilityFailureReport:
    unsupported:tuple[CapabilityRequest,...]
    blockers:tuple[str,...]
    warnings:tuple[str,...]
    passed:bool
    accepted:bool=False

def evaluate_capabilities(requests,registry):
    unsupported=[]; blockers=[]; warnings=[]
    for r in requests:
        if not registry.supports(r.capability_id,r.element_type,r.requested_action,r.target_profile):
            unsupported.append(r); key=f"{r.capability_id}:{r.element_id}:{r.requested_action}:{r.target_profile}"
            (blockers if r.required else warnings).append(('unsupported_required:' if r.required else 'unsupported_optional:')+key)
    return CapabilityFailureReport(tuple(unsupported),tuple(sorted(blockers)),tuple(sorted(warnings)),not blockers,False)

def require_no_required_unsupported(report):
    if report.blockers: raise SceneIRCapabilityError('required capability unsupported')
    return True
