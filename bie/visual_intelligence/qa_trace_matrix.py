from dataclasses import dataclass
from hashlib import sha256
import json
class TraceMatrixError(ValueError): pass
@dataclass(frozen=True)
class TraceRow:
    visual_id:str; required:bool; source_refs:tuple[str,...]; reasoning_refs:tuple[str,...]; representation_id:str|None; grammar_element_id:str|None; layout_node_id:str|None; text_id:str|None; asset_id:str|None; qa_ids:tuple[str,...]; claim_supported:bool=True
@dataclass(frozen=True)
class TraceAudit:
    passed:bool; orphan_visual_ids:tuple[str,...]; unsupported_visual_ids:tuple[str,...]; lost_required_ids:tuple[str,...]; missing_qa_ids:tuple[str,...]; fingerprint:str; review_required:bool=True; accepted:bool=False
def audit_trace(rows):
    rows=tuple(rows)
    if not rows: raise TraceMatrixError('rows required')
    if len({r.visual_id for r in rows})!=len(rows): raise TraceMatrixError('duplicate visual IDs')
    orphan=[];unsupported=[];lost=[];missing=[]
    for r in rows:
        if not r.source_refs or not r.reasoning_refs: orphan.append(r.visual_id)
        if not r.claim_supported: unsupported.append(r.visual_id)
        if r.required and not any((r.grammar_element_id,r.layout_node_id,r.text_id,r.asset_id)): lost.append(r.visual_id)
        if not r.qa_ids: missing.append(r.visual_id)
    p={'orphan':sorted(orphan),'unsupported':sorted(unsupported),'lost':sorted(lost),'missing':sorted(missing)}
    return TraceAudit(not any(p.values()),tuple(sorted(orphan)),tuple(sorted(unsupported)),tuple(sorted(lost)),tuple(sorted(missing)),sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest(),True,False)
def require_trace_pass(a):
    if not a.passed: raise TraceMatrixError('element-level trace audit failed')
    return True
