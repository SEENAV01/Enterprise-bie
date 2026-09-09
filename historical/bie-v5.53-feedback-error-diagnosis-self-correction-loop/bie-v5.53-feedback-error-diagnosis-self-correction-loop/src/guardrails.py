def loop_guard(iteration,max_iterations=3,
               repeated_failure_count=2):
    if iteration>=max_iterations:
        return {"allowed":False,"reason":"MAX_ITERATIONS"}
    if repeated_failure_count>=3:
        return {"allowed":False,"reason":"REPEATED_FAILURE"}
    return {"allowed":True,"reason":None}

def should_escalate(diagnosis):
    return diagnosis.get("severity")=="CRITICAL" or            diagnosis.get("confidence",1) < 0.4
