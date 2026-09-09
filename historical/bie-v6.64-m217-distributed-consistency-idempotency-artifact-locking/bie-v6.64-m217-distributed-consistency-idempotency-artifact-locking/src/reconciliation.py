def reconcile(states):
    if not states:
        return {"status":"EMPTY","canonical":None}
    versions=[x["version"] for x in states]
    max_version=max(versions)
    candidates=[x for x in states if x["version"]==max_version]
    values={repr(x["value"]) for x in candidates}
    if len(values)>1:
        return {"status":"CONFLICT","canonical":None,
                "candidates":candidates}
    return {"status":"CONSISTENT","canonical":candidates[0]}
