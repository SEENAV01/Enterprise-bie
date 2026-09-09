def ordering_policy(scope,
                   ordered=True,
                   key_field=None):
    return {"scope":scope,
            "ordered":ordered,
            "key_field":key_field}

def ordering_key(event_record,
                 policy):
    field=policy.get("key_field")
    return event_record.get(field) if field else None
