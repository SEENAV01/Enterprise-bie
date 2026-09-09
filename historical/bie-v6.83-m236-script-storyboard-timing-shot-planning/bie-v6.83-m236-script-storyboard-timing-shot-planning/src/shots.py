def shot_plan(storyboard_items,timings):
    tm={x["segment_id"]:x for x in timings}
    return [{**s,"start":tm[s["segment_id"]]["start"],
             "end":tm[s["segment_id"]]["end"]}
            for s in storyboard_items if s["segment_id"] in tm]

def validate_shots(shots):
    return {"passed":bool(shots) and all(x["end"]>x["start"] for x in shots),
            "errors":[]}
