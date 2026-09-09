from verification import verify_claim,verification_gate
from contradictions import detect_explicit_contradictions
from representations import consistency_check

def compile_integrity_report(claims,evidence_items,
                             contradiction_pairs=None,
                             representation_groups=None):
    results=[verify_claim(c,evidence_items) for c in claims]
    gate=verification_gate(results)
    contradictions=detect_explicit_contradictions(contradiction_pairs or [])
    consistency=[consistency_check(g) for g in (representation_groups or [])]
    errors=[]
    if contradictions: errors.append("CONTRADICTIONS_FOUND")
    if any(not x.get("valid") for x in consistency): errors.append("REPRESENTATION_MISMATCH")
    return {"schema_version":"5.30",
            "claim_results":results,
            "verification_gate":gate,
            "contradictions":contradictions,
            "representation_checks":consistency,
            "quality_gate":{"valid":gate["passed"] and not errors,
                            "errors":errors+
                            ([] if gate["passed"] else ["UNSUPPORTED_CLAIMS"])}}
