def transfer(transfer_id,content_id,
             source,destination,size_bytes):
    return {"transfer_id":transfer_id,
            "content_id":content_id,
            "source":source,"destination":destination,
            "size_bytes":size_bytes,"status":"PLANNED"}

def complete_transfer(record,checksum_verified=True):
    out=dict(record)
    out["checksum_verified"]=checksum_verified
    out["status"]="COMPLETE" if checksum_verified else "FAILED"
    return out
