def tokenization_policy(fields, vault_ref,
                       reversible=False):
    return {"fields":fields,"vault_ref":vault_ref,
            "reversible":reversible}

def protected(policy, field):
    return field in policy["fields"]
