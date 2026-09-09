def semantic_binding(binding_id,semantic_ref,
                   target_ref,binding_type="DATA"):
    return {"binding_id":binding_id,
            "semantic_ref":semantic_ref,
            "target_ref":target_ref,
            "binding_type":binding_type}

def resolve_bindings(bindings,semantic_values):
    resolved=[]
    for b in bindings:
        if b.get("semantic_ref") in semantic_values:
            x=dict(b)
            x["value"]=semantic_values[b["semantic_ref"]]
            resolved.append(x)
    return resolved
