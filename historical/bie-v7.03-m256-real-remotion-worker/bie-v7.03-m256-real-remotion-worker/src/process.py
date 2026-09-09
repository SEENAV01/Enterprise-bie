def create_process_spec(command,args=None,cwd=None,env=None):
    return {"command":command,"args":args or [],"cwd":cwd,"env":env or {},
            "status":"READY"}

def validate_process_spec(spec):
    errors=[]
    if not spec.get("command"): errors.append("COMMAND_MISSING")
    if not isinstance(spec.get("args"),list): errors.append("ARGS_INVALID")
    return {"valid":not errors,"errors":errors}
