def execution_key(job_id, attempt=0):
    return f"{job_id}:attempt:{attempt}"

def accept_once(store, key, result):
    if key in store: return {"accepted":False,"result":store[key]}
    store[key]=result
    return {"accepted":True,"result":result}
