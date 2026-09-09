def validation_rule(rule_id,kind,target,value=None,severity="required"):
    return {"rule_id":rule_id,"kind":kind,"target":target,
            "value":value,"severity":severity}

def validate_contract(contract):
    errors=[]
    if not contract.get("asset_ref"):
        errors.append("ASSET_REFERENCE_MISSING")
    if not contract.get("outputs"):
        errors.append("OUTPUT_SPEC_MISSING")
    if not contract.get("validation"):
        errors.append("VALIDATION_SPEC_MISSING")
    return sorted(set(errors))
