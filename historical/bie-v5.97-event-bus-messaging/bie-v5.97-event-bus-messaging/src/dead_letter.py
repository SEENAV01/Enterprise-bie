def dead_letter(message_id,event,
                reason,attempts):
    return {"message_id":message_id,
            "event":event,"reason":reason,
            "attempts":attempts,"status":"DEAD_LETTER"}

def is_dead_letter(record):
    return record.get("status")=="DEAD_LETTER"
