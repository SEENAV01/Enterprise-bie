from budgets import budget_check
from isolation import validate_isolation

def compile_execution(envelope,usage=None,isolation=None):
    usage=usage or {}
    isolation=isolation or {}
    budget=budget_check(usage,envelope.get("budgets",{}))
    iso=validate_isolation(isolation)
    return {"schema_version":"5.57","envelope":envelope,
            "budget_check":budget,"isolation_check":iso,
            "quality_gate":{"allowed":budget["allowed"] and iso["valid"],
                            "errors":budget["exceeded"]+
                            iso["missing_or_disabled"]}}
