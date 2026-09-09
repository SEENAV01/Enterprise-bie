def termination(status,reason,exit_code=None,
               duration_seconds=None):
    return {"status":status,"reason":reason,
            "exit_code":exit_code,
            "duration_seconds":duration_seconds}

def timed_out(duration_seconds,limits):
    return duration_seconds > limits.get("timeout_seconds",0)
