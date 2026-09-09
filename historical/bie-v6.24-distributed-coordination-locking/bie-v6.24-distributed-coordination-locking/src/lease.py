def lease(resource_id,owner,
          expires_at,epoch=1):
    return {"resource_id":resource_id,
            "owner":owner,
            "expires_at":expires_at,
            "epoch":epoch,
            "status":"HELD"}

def valid(record,now):
    return record["status"]=="HELD" and now < record["expires_at"]
