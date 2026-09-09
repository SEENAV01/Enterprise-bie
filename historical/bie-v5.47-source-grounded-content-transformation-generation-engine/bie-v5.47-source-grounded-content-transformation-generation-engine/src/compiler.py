from constraints import validate_output

def compile_transformation(request,outputs,source_fragments):
    source_ids={f["fragment_id"] for f in source_fragments}
    errors=[]
    for o in outputs:
        for ref in o.get("source_refs",[]):
            if ref not in source_ids:
                errors.append("OUTPUT_SOURCE_REFERENCE_MISSING")
        errors.extend(validate_output(o,request.get("constraints",[])))
        if not request.get("allow_generation",True) and o.get("generated_refs"):
            errors.append("GENERATION_NOT_ALLOWED")
    return {"schema_version":"5.47",
            "request":request,"outputs":outputs,
            "source_fragments":source_fragments,
            "quality_gate":{"valid":not errors,
                            "errors":sorted(set(errors))}}
