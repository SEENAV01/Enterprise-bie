def admission(subject, resource, requested,
              available, quota_ok=True, budget_ok=True):
    admitted = requested <= available and quota_ok and budget_ok
    return {"subject":subject,"resource":resource,
            "requested":requested,"available":available,
            "quota_ok":quota_ok,"budget_ok":budget_ok,
            "decision":"ADMIT" if admitted else "REJECT"}

def admitted(record):
    return record["decision"]=="ADMIT"
