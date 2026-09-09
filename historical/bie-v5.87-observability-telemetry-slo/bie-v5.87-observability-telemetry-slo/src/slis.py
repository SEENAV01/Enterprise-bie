def availability_sli(good,total):
    return good/total if total else 1.0

def error_rate(errors,total):
    return errors/total if total else 0.0

def latency_sli(latencies,threshold):
    vals=list(latencies)
    if not vals: return 1.0
    return sum(x<=threshold for x in vals)/len(vals)
