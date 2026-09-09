from reconciliation import compare_claims
from evidence_packet import evidence_packet

def compile_reconciliation(concept_id,claims,evidence,
                            contradictions=None,unresolved=False):
    groups=compare_claims(claims)
    packet=evidence_packet(concept_id,claims,evidence,contradictions,unresolved)
    errors=[]
    if unresolved: errors.append("UNRESOLVED_EVIDENCE")
    if contradictions: errors.append("CONTRADICTIONS_PRESENT")
    return {"schema_version":"5.19","claim_groups":groups,
            "evidence_packet":packet,
            "quality_gate":{"valid":not errors,"errors":errors}}
