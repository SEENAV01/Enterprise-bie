def quality_gate(gate_id,required_categories=None,
                fail_on=("FAIL",)):
    return {"gate_id":gate_id,
            "required_categories":list(required_categories or []),
            "fail_on":list(fail_on)}

def evaluate_gate(results,gate):
    required=set(gate.get("required_categories",[]))
    present={r.get("category") for r in results}
    missing=sorted(required-present)
    failures=[r for r in results if r.get("status") in gate.get("fail_on",[])]
    return {"gate_id":gate["gate_id"],"passed":not missing and not failures,
            "missing_categories":missing,
            "failures":failures}
