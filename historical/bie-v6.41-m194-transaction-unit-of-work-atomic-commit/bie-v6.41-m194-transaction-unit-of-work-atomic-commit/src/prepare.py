def prepare(tx_id, read_write_set,
            validation_token=None):
    return {"tx_id":tx_id,"read_write_set":read_write_set,
            "validation_token":validation_token,
            "status":"PREPARED"}

def prepared(record):
    return record["status"]=="PREPARED"
