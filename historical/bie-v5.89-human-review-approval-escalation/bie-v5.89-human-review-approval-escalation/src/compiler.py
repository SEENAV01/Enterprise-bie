from decision import review_decision
from evidence import evidence_packet
from release_gate import review_release_gate

def compile_review(item_id,artifact,reviewer_id,
                   decision,rationale,automated_pass=True,
                   evidence=None):
    packet=evidence_packet(item_id,artifact,
                           evaluations=evidence or [])
    d=review_decision(item_id,reviewer_id,decision,
                      rationale,{"packet":item_id})
    gate=review_release_gate(automated_pass,d)
    return {"schema_version":"5.89",
            "evidence_packet":packet,
            "decision":d,"release":gate,
            "quality_gate":{"valid":True,"errors":[]}}
