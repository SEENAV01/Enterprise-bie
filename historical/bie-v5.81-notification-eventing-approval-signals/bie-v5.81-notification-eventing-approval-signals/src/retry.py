def retry_delay(attempt,base=1,max_delay=300):
    return min(max_delay,base*(2**max(0,attempt-1)))

def delivery_state(attempt,status,error=None):
    return {"attempt":attempt,"status":status,"error":error}
