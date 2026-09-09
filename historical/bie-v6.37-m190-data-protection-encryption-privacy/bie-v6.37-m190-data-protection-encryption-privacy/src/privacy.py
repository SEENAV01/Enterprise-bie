def privacy_policy(purpose, lawful_basis=None,
                  minimization=True, consent_required=False):
    return {"purpose":purpose,"lawful_basis":lawful_basis,
            "minimization":minimization,
            "consent_required":consent_required}

def purpose_allowed(policy, purpose):
    return policy["purpose"]==purpose
