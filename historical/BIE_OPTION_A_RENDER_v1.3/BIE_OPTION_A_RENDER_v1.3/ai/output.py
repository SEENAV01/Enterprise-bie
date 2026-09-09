def validate_structured_output(output, required_fields):
    errors=[f"FIELD_REQUIRED:{f}" for f in required_fields if f not in output]
    return {"valid":not errors,"errors":errors}

def normalize_output(output):
    return {str(k):v for k,v in output.items()}
