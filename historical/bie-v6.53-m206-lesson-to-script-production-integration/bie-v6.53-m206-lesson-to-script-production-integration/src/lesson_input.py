def lesson_input(lesson_id, title, objectives, prerequisites=None,
                 duration_min=None, evidence_ids=None):
    if not lesson_id or not objectives:
        raise ValueError("INVALID_LESSON_INPUT")
    return {"lesson_id":lesson_id,"title":title,"objectives":objectives,
            "prerequisites":prerequisites or [],
            "duration_min":duration_min,"evidence_ids":evidence_ids or []}

def valid(item):
    return bool(item["lesson_id"] and item["objectives"])
