def idempotency_key(scope,
                    operation,
                    key):
    return {"scope":scope,
            "operation":operation,
            "key":key}

def same_operation(a,b):
    return (a["scope"]==b["scope"] and
            a["operation"]==b["operation"] and
            a["key"]==b["key"])
