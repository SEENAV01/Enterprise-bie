def check(name,passed,details=None,severity="ERROR"):
    return {"name":name,"passed":bool(passed),
            "severity":severity,"details":details or {}}

def run_checks(checks):
    results=[c() if callable(c) else c for c in checks]
    return {"results":results,
            "passed":all(r["passed"] for r in results)}
