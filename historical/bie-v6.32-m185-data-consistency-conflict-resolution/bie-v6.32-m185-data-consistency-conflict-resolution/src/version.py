def state_version(value,clock,writer=None):
    return {"value":value,"clock":clock,"writer":writer}

def versioned(record):
    return "clock" in record and record["clock"] is not None
