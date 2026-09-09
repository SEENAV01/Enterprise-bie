def dead_letter_policy(queue_name,
                      after_attempts=5,
                      reason_codes=None):
    return {"queue":queue_name,
            "after_attempts":after_attempts,
            "reason_codes":reason_codes or [],
            "enabled":True}

def dead_lettered(record,attempt):
    return record["enabled"] and attempt >= record["after_attempts"]
