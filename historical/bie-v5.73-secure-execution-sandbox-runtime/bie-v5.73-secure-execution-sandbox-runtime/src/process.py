def process_policy(max_processes=16,allowed_executables=None):
    return {"max_processes":max_processes,
            "allowed_executables":allowed_executables or []}

def executable_allowed(policy,executable):
    return executable in set(policy.get("allowed_executables",[]))
