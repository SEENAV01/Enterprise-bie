def acknowledgment(message_id,consumer_id,
                    status="ACK",offset=None):
    return {"message_id":message_id,
            "consumer_id":consumer_id,
            "status":status,"offset":offset}

def acknowledged(record):
    return record.get("status")=="ACK"
