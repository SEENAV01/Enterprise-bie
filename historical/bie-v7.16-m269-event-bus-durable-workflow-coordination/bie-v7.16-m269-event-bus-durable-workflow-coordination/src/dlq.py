def dead_letter(queue,event,error,attempt):
    queue.append({"event":event,"error":error,"attempt":attempt,"status":"DEAD_LETTER"})
    return queue[-1]

def retryable(attempt,max_attempts=3):
    return attempt < max_attempts
