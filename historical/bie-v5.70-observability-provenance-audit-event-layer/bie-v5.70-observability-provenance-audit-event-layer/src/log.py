def append_event(log,event):
    out=list(log)
    out.append(event)
    return out

def validate_append_only(previous_log,current_log):
    if len(current_log)<len(previous_log): return False
    return current_log[:len(previous_log)]==previous_log
