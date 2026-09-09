def certificate(cert_id,subject,
               issuer,not_before,
               not_after,version=1,
               status="ACTIVE"):
    return {"cert_id":cert_id,
            "subject":subject,
            "issuer":issuer,
            "not_before":not_before,
            "not_after":not_after,
            "version":version,
            "status":status}

def valid_at(record,now):
    return (record["status"]=="ACTIVE" and
            record["not_before"] <= now < record["not_after"])
