def compare_metrics(current,baseline,allowed_drop=0.0):
    changes={}
    for key,value in current.items():
        if key in baseline:
            changes[key]={
              "current":value,
              "baseline":baseline[key],
              "delta":value-baseline[key],
              "regressed":value < baseline[key]-allowed_drop}
    return changes

def release_regression(changes):
    return not any(v["regressed"] for v in changes.values())
