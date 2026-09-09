def ownership(resource,owner,
              fencing_token,lease_id):
    return {"resource":resource,"owner":owner,
            "fencing_token":fencing_token,
            "lease_id":lease_id}

def owns(record,owner,token):
    return (record.get("owner")==owner and
            record.get("fencing_token")==token)
