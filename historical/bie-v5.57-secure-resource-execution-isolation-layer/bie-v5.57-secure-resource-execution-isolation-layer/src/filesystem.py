def filesystem_policy(input_roots=None,output_roots=None,
                      writable_roots=None):
    return {"input_roots":input_roots or [],
            "output_roots":output_roots or [],
            "writable_roots":writable_roots or []}

def path_allowed(policy,path,mode="read"):
    roots=policy.get("input_roots",[]) if mode=="read" else           policy.get("writable_roots",[])
    return any(path.startswith(r) for r in roots)
