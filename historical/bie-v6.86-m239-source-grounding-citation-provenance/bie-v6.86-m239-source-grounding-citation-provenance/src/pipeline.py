from sources import source,validate_source
from evidence import evidence,validate_evidence
from claims import grounded_claim,verify_claim
from citations import citation_map,coverage
from provenance import provenance_record,provenance_chain

def build_grounding_runtime():
    sources=[source("SRC-1","textbook://chapter1","Physics Textbook","Example Publisher","p.12")]
    evidence_items=[evidence("E-1","SRC-1","Electric charge is a physical property.","p.12")]
    claims=[grounded_claim("C-1","Electric charge is a physical property.",["E-1"],0.98)]
    source_checks=[validate_source(s) for s in sources]
    evidence_checks=[validate_evidence(e",{s["source_id"] for s in sources}) for e in []]
    evidence_checks=[validate_evidence(e,{s["source_id"] for s in sources}) for e in evidence_items]
    eb={e["evidence_id"]:e for e in evidence_items}
    claim_checks=[verify_claim(c,eb) for c in claims]
    cmap=citation_map(claims,eb)
    cov=coverage(claims,eb)
    prov=[provenance_record("C-1","grounded_claim",[],["SRC-1"])]
    return {"schema_version":"6.86","sources":sources,"source_validation":source_checks,
            "evidence":evidence_items,"evidence_validation":evidence_checks,
            "claims":claims,"claim_validation":claim_checks,"citation_map":cmap,
            "coverage":cov,"provenance":prov,
            "grounding_gate":{"valid":all(x["passed"] for x in source_checks+evidence_checks+claim_checks)
                and cov["coverage"]>=1.0,"errors":[]}}
