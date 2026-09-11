from __future__ import annotations
from bie.reasoning.grounded_result import GroundedResult,inference,evidence
TASK_ID="BIE-RE-TEMP-017"
def audit_temporal_lineage(results,refs):
    refs=evidence(refs); results=tuple(results)
    if not results: raise ValueError("At least one temporal result required")
    known={r.artifact_id for r in refs}; used=set(); weak=[]; review=[]
    for r in results:
        if not isinstance(r,GroundedResult) or not r.operation.startswith("temporal."): raise ValueError("Temporal GroundedResult required")
        ids={x.artifact_id for x in r.evidence_refs}; used|=ids
        if not ids<=known: raise ValueError("Result evidence missing from audit evidence set")
        if r.confidence<0.75: weak.append(r.result_id)
        if r.requires_review: review.append(r.result_id)
    missing=sorted(known-used)
    value={"result_count":len(results),"used_evidence_ids":sorted(used),"unused_evidence_ids":missing,"weak_result_ids":sorted(weak),"review_result_ids":sorted(review),"coverage":len(used)/len(known)}
    return inference(TASK_ID,"temporal.lineage_audit",{"result_ids":[r.result_id for r in results]},value,refs,status="AMBIGUOUS" if review or missing else "RESOLVED",uncertainty=("Some evidence is unused or some temporal results require review",) if review or missing else ())
