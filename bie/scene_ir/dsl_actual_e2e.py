from dataclasses import dataclass
from .ani_dsl_adopter import adopt_ani_handoff
from .spatial_resolution import resolve_spatial_constraints
from .temporal_resolution import resolve_temporal_consistency
from .interaction_resolution import resolve_interactions
from .accessibility_merge import merge_accessibility
from .compiler_capability_resolution import resolve_compiler_capabilities
from .provenance_resolution import resolve_provenance
from .asset_contract import resolve_assets
from .document_integrity import inspect_document_integrity
from .dsl_orchestrator import validate_scene_ir_document
from .compiler_preflight_handoff import build_compiler_preflight_handoff
@dataclass(frozen=True)
class DSLE2EResult:
    scene_id:str;final_fingerprint:str;stage_statuses:tuple[tuple[str,str],...];compiler_handoff_id:str|None
    blockers:tuple[str,...];status:str;compile_status:str="NOT_RUN";render_status:str="NOT_RUN";accepted:bool=False
def run_ani_to_compiler_ready(*,ani_handoff,scene_id,title,duration_ms,element_catalog,ani_revision,source_registry,reasoning_registry,asset_registry,compiler_registry,target_profile="web"):
    stages=[]; blockers=[]
    d,_=adopt_ani_handoff(ani_handoff,scene_id=scene_id,title=title,duration_ms=duration_ms,element_catalog=element_catalog,ani_revision=ani_revision);stages.append(("ani_adoption","PASS"))
    d,s=resolve_spatial_constraints(d);stages.append(("spatial","PASS" if s.passed else "BLOCK"));blockers += ["spatial:"+x for x in s.blockers]
    d,t=resolve_temporal_consistency(d);stages.append(("temporal","PASS" if t.passed else "BLOCK"));blockers += ["temporal:"+x for x in t.blockers]
    i=resolve_interactions(d);stages.append(("interaction","PASS" if i.passed else "BLOCK"));blockers += ["interaction:"+x for x in i.blockers]
    d,a=merge_accessibility(d);stages.append(("accessibility","PASS" if a.passed else "BLOCK"));blockers += ["accessibility:"+x for x in a.blockers]
    p=resolve_provenance(d,source_registry,reasoning_registry);stages.append(("provenance","PASS" if p.passed else "BLOCK"));blockers += ["provenance:"+x for x in p.blockers]
    ar=resolve_assets(d,asset_registry);stages.append(("assets","PASS" if ar.passed else "BLOCK"));blockers += ["assets:"+x for x in ar.blockers]
    integ=inspect_document_integrity(d);stages.append(("integrity","PASS" if integ.passed else "BLOCK"));blockers += ["integrity:"+x for x in integ.blockers]
    cap=resolve_compiler_capabilities(d,compiler_registry,target_profile);stages.append(("capability","PASS" if cap.passed else "BLOCK"));blockers += ["capability:"+x for x in cap.blockers]
    gate=validate_scene_ir_document(d);stages.append(("dsl_gate","PASS" if gate.passed else "BLOCK"));blockers += ["dsl_gate:"+x for x in gate.blockers]
    h=build_compiler_preflight_handoff(d,target_profile=target_profile,provenance_receipt=p,asset_receipt=ar,integrity_receipt=integ,accessibility_receipt=a,capability_receipt=cap);stages.append(("compiler_preflight","PASS" if h.compiler_ready else "BLOCK"));blockers += ["compiler_preflight:"+x for x in h.blockers]
    status="PASS" if not blockers else "BLOCK"
    return d,h,DSLE2EResult(d.scene_id,d.fingerprint,tuple(stages),h.handoff_id if h.compiler_ready else None,tuple(sorted(set(blockers))),status,"NOT_RUN","NOT_RUN",False)
