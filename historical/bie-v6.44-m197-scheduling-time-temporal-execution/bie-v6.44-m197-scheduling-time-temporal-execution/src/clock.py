def clock(clock_id="system", timezone="UTC", monotonic=False):
    return {"clock_id":clock_id,"timezone":timezone,
            "monotonic":monotonic}

def valid(record):
    return bool(record["clock_id"] and record["timezone"])
