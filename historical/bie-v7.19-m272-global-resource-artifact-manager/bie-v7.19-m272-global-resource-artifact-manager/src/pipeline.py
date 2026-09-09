from identity import content_id,artifact_id
from artifacts import register_artifact,resolve
from dedup import deduplicate,canonical_artifact
from lineage import add_lineage,ancestors
from retention import retention_decision,garbage_candidates

def build_m272_runtime():
    store={}
    data=b"BIE artifact payload"
    h=content_id(data)
    a1=artifact_id("course","lesson-1-render","v1")
    a2=artifact_id("course","lesson-1-render-copy","v1")
    r1=register_artifact(store,a1,h,{"source":"render","expires_at":100})
    r2=register_artifact(store,a2,h,{"source":"cache","expires_at":100})
    graph={}
    add_lineage(graph,a1,["source:lesson-1"])
    add_lineage(graph,"release:lesson-1",[a1])
    lineage=ancestors(graph,"release:lesson-1")
    duplicate=deduplicate(store,h)
    canonical=canonical_artifact(store,h)
    retention=retention_decision(store[a1],101)
    candidates=garbage_candidates(store,101)
    return {"schema_version":"7.19","artifacts":[r1,r2],
            "resolved":resolve(store,a1),"content_hash":h,
            "deduplication":{"count":len(duplicate),"canonical":canonical},
            "lineage":{"release":"release:lesson-1","ancestors":lineage},
            "retention":{"decision":retention,"garbage_candidates":candidates},
            "artifact_gate":{"valid":r1["created"] and r2["created"] and
                             len(duplicate)==2 and canonical is not None and
                             not retention["retain"],"errors":[]}}
