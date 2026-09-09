def calendar_window(start,end,
                    weekdays=None):
    return {"start":start,"end":end,
            "weekdays":weekdays or []}

def contains(window,instant):
    return window["start"] <= instant <= window["end"]
