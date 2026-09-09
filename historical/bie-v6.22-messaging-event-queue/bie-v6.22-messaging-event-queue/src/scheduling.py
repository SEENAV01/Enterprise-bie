def scheduled_delivery(message_id,
                       deliver_at,
                       timezone="UTC"):
    return {"message_id":message_id,
            "deliver_at":deliver_at,
            "timezone":timezone,
            "status":"SCHEDULED"}

def due(record,now):
    return now >= record["deliver_at"]
