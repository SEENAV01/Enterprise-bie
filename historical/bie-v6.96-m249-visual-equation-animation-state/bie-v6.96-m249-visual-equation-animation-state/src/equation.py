def create_equation(eq_id,expression,variables=None):
    return {"equation_id":eq_id,"expression":expression,"variables":variables or {}}

def apply_equation_step(equation,operation,result_expression):
    return {"equation_id":equation["equation_id"],"from":equation["expression"],
            "operation":operation,"to":result_expression}

def validate_equation_step(step,expected_to):
    ok=step.get("to")==expected_to
    return {"valid":ok,"reason":"MATCH" if ok else "MISMATCH"}
