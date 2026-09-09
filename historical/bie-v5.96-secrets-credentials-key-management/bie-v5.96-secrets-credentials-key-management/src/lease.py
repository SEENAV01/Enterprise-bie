def credential_lease(lease_id,grant_id,
                     issued_at,expires_at):
    return {"lease_id":lease_id,"grant_id":grant_id,
            "issued_at":issued_at,"expires_at":expires_at}

def valid_lease(lease,now):
    return now<lease["expires_at"]
