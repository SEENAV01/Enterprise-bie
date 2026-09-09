def epoch(term, epoch_id=None):
    if term < 0:
        raise ValueError("INVALID_TERM")
    return {"term":term,"epoch_id":epoch_id or str(term)}

def current(record, term):
    return record["term"]==term
