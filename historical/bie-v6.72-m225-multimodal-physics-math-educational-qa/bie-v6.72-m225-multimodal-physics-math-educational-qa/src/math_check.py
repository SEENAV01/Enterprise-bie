def check_equation(lhs,rhs,tolerance=1e-9):
    try:
        a,b=float(lhs),float(rhs); err=abs(a-b)
        return {"passed":err<=tolerance,"error":err,"tolerance":tolerance}
    except (TypeError,ValueError):
        return {"passed":False,"error":"NON_NUMERIC_EXPRESSION"}
def check_relation(observed,expected,tolerance=0.05):
    err=abs(observed-expected)
    return {"passed":err<=tolerance,"error":err,"tolerance":tolerance}
