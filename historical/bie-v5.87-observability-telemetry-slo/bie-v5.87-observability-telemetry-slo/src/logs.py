import time, json

def log(level,message,**fields):
    record={"timestamp":time.time(),"level":level,
            "message":message,**fields}
    return record

def serialize(record):
    return json.dumps(record,sort_keys=True)
