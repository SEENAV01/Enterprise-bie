def budget(budget_id, subject, resource,
           amount, period=None):
    if amount < 0:
        raise ValueError("INVALID_BUDGET")
    return {"budget_id":budget_id,"subject":subject,
            "resource":resource,"amount":amount,
            "period":period,"status":"ACTIVE"}

def sufficient(record, requested, spent=0):
    return spent + requested <= record["amount"]
