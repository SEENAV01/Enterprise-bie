def encryption_policy(required=True, algorithm=None,
                     at_rest=True, in_transit=True):
    return {"required":required,"algorithm":algorithm,
            "at_rest":at_rest,"in_transit":in_transit}

def compliant(policy, algorithm=None, at_rest=True, in_transit=True):
    if not policy["required"]:
        return True
    if policy["algorithm"] and policy["algorithm"]!=algorithm:
        return False
    return at_rest and in_transit
