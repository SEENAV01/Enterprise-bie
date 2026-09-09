from factuality import validate_claim
from formulas import verify_formula
from definitions import verify_definition
from consistency import consistency_check,cross_reference

def run_content_qa(claims,definitions,formulas,require_sources=False):
    checks=[]
    checks += [validate_claim(c,require_sources) for c in claims]
    checks += [verify_definition(d) for d in definitions]
    checks += [verify_formula(f) for f in formulas]
    consistency=consistency_check(claims)
    refs=cross_reference(claims,definitions,formulas)
    passed=all(x["passed"] for x in checks) and consistency["passed"]
    return {"passed":passed,"checks":checks,"consistency":consistency,
            "cross_reference":refs}
