def idempotency_record(key,request_hash,
                       response=None,status="IN_PROGRESS"):
    return {"key":key,"request_hash":request_hash,
            "response":response,"status":status}

def reusable(record,request_hash):
    return (record is not None and
            record.get("request_hash")==request_hash and
            record.get("status")=="COMPLETED")
