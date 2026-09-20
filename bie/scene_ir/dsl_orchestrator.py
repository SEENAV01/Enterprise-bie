from dataclasses import dataclass
from .unified_scene_ir_codec import decode_scene_ir
from .scene_ir_registry import default_registry
from .schema_validation import validate_schema_shape
from .semantic_validation import validate_semantics
from .reference_validation import validate_references
from .temporal_validation import validate_temporal
from .spatial_validation import validate_spatial
from .accessibility_validation import validate_accessibility
from .trace_validation import validate_source_reasoning_trace

@dataclass(frozen=True)
class DSLGateReport:
    scene_id:str;fingerprint:str;validator_reports:tuple;blockers:tuple[str,...];warnings:tuple[str,...];passed:bool;accepted:bool=False

def validate_scene_ir_document(x,registry=None):
    try:
        doc=decode_scene_ir(x) if not hasattr(x,"to_dict") else x
    except Exception as e:
        return DSLGateReport("<decode-failed>","",(),("DECODE:"+str(e),),(),False,False)
    registry=registry or default_registry()
    try:
        registry.normalize_document(doc)
    except Exception as e:
        return DSLGateReport(doc.scene_id,doc.fingerprint,(),("REGISTRY:"+str(e),),(),False,False)
    validators=(validate_schema_shape,validate_semantics,validate_references,validate_temporal,validate_spatial,validate_accessibility,validate_source_reasoning_trace)
    reports=tuple(v(doc.to_dict()) for v in validators)
    blockers=[];warnings=[]
    for r in reports:
        for i in r.issues:
            msg=f"{r.validator_id}:{i.code}:{i.path}"
            (blockers if i.severity=="ERROR" else warnings).append(msg)
    return DSLGateReport(doc.scene_id,doc.fingerprint,reports,tuple(sorted(set(blockers))),tuple(sorted(set(warnings))),not blockers,False)

def require_dsl_gate(r):
    if not r.passed:raise ValueError("DSL gate failed")
    return True
