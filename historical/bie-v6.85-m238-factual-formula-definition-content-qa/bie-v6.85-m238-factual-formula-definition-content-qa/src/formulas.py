import ast, math

def formula(formula_id,expression,variables=None,units=None):
    return {"formula_id":formula_id,"expression":expression,
            "variables":variables or [],"units":units or {}}

def verify_formula(f):
    errors=[]
    try: ast.parse(f["expression"],mode="eval")
    except Exception: errors.append("INVALID_EXPRESSION")
    if not f.get("variables"): errors.append("MISSING_VARIABLES")
    return {"passed":not errors,"errors":errors}
