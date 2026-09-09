def commit(tx_id, commit_token=None):
    return {"tx_id":tx_id,"commit_token":commit_token,
            "status":"COMMITTED"}

def committed(record):
    return record["status"]=="COMMITTED"
