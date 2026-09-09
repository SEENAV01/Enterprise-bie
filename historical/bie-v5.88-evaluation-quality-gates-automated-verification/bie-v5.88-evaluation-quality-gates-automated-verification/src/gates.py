def gate(name,threshold=0.0,required_checks=None):
    return {"name":name,"threshold":threshold,
            "required_checks":required_checks or []}

def evaluate_gate(gate_record,evaluation,check_results):
    checks={r["name"]:r["passed"] for r in check_results}
    required=all(checks.get(x,False)
                 for x in gate_record["required_checks"])
    passed=(evaluation["score"]>=gate_record["threshold"]
            and evaluation["passed"] and required)
    return {"gate":gate_record["name"],
            "passed":passed,
            "score":evaluation["score"],
            "required_checks_passed":required}
