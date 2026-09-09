MODES={"static","slow_push_in","slow_pull_out","pan","zoom","focus","follow_path"}

def camera_plan(mode="static", focus=None, duration_ms=None):
    if mode not in MODES: raise ValueError("Unsupported camera mode")
    return {"mode":mode,"focus":focus,"duration_ms":duration_ms}
