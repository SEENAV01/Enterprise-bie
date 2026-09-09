def separation_check(requester,approvers):
    return {"valid":requester not in set(approvers),
            "reason":"SEPARATION_OF_DUTIES" if requester in set(approvers)
                     else "OK"}
