def validate_orchestration(result):
    errors=result.get("quality_gate",{}).get("errors",[])
    return {"valid":not errors,"errors":errors}
