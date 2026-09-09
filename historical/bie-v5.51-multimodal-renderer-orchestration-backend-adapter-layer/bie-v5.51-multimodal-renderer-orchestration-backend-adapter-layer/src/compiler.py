from routing import route_candidates,choose_backend

def compile_renderer_plan(contracts,backends,backend_signals=None,
                          weights=None):
    jobs=[]
    errors=[]
    for c in contracts:
        candidates=route_candidates(c,backends)
        chosen=choose_backend(c,backends,backend_signals,weights)
        if not candidates:
            errors.append("NO_COMPATIBLE_BACKEND")
        jobs.append({"contract_ref":c["contract_id"],
                     "candidate_backends":[b["backend_id"] for b in candidates],
                     "selected_backend":chosen["backend_id"] if chosen else None})
    return {"schema_version":"5.51","contracts":contracts,
            "backends":backends,"jobs":jobs,
            "quality_gate":{"valid":not errors,
                            "errors":sorted(set(errors))}}
