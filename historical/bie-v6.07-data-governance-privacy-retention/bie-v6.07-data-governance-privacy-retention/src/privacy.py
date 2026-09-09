def privacy_label(category,
                 contains_pii=False,
                 special_handling=False):
    return {"category":category,
            "contains_pii":contains_pii,
            "special_handling":special_handling}

def requires_protection(record):
    return bool(record.get("contains_pii") or
                record.get("special_handling"))
