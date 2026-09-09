def execution_window(start_at,
                    end_at,
                    timezone="UTC"):
    if end_at < start_at:
        raise ValueError("INVALID_EXECUTION_WINDOW")
    return {"start_at":start_at,
            "end_at":end_at,
            "timezone":timezone}

def inside(record,now):
    return record["start_at"] <= now <= record["end_at"]
