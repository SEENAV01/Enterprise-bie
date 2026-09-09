def override_record(review_id,reviewer_id,
                   original_gate,reason,authority,
                   timestamp):
    return {"review_id":review_id,"reviewer_id":reviewer_id,
            "original_gate":original_gate,"reason":reason,
            "authority":authority,"timestamp":timestamp,
            "type":"EXPLICIT_OVERRIDE"}

def override_allowed(record,minimum_authority="SENIOR_REVIEWER"):
    return bool(record.get("reason")) and            record.get("authority")==minimum_authority
