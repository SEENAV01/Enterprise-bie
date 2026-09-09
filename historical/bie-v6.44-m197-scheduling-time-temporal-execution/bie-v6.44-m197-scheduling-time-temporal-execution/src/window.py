def temporal_window(start_at, end_at,
                   inclusive_start=True, inclusive_end=False):
    return {"start_at":start_at,"end_at":end_at,
            "inclusive_start":inclusive_start,
            "inclusive_end":inclusive_end}

def contains(record, timestamp):
    left = timestamp >= record["start_at"] if record["inclusive_start"] else timestamp > record["start_at"]
    right = timestamp <= record["end_at"] if record["inclusive_end"] else timestamp < record["end_at"]
    return left and right
