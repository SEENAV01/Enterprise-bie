def filesystem_policy(read_roots=None,write_root="/artifacts",
                     allow_delete=False):
    return {"read_roots":read_roots or [],
            "write_root":write_root,
            "allow_delete":allow_delete}

def write_allowed(policy,path):
    root=policy.get("write_root","")
    return bool(root) and path.startswith(root+"/")
