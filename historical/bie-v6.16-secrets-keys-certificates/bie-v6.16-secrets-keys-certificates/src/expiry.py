def expiry_check(item_id,item_type,
                expires_at,now):
    return {"item_id":item_id,
            "item_type":item_type,
            "expires_at":expires_at,
            "now":now,
            "expired":now >= expires_at}

def safe(record):
    return not record["expired"]
