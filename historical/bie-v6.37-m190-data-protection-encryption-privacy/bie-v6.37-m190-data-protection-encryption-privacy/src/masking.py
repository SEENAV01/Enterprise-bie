def masking_policy(fields, strategy="REDACT",
                  preserve_length=False):
    if strategy not in {"REDACT","PARTIAL","HASH","TOKENIZE"}:
        raise ValueError("INVALID_MASKING_STRATEGY")
    return {"fields":fields,"strategy":strategy,
            "preserve_length":preserve_length}

def applies(policy, field):
    return field in policy["fields"]
