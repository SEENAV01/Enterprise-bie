def burn_rate(observed_error_ratio,
               allowed_error_ratio):
    if allowed_error_ratio<=0:
        return float("inf") if observed_error_ratio>0 else 0
    return observed_error_ratio/allowed_error_ratio

def exceeds(rate,threshold):
    return rate>=threshold
