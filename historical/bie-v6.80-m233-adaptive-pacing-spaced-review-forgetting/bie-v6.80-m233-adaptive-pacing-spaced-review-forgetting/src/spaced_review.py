def next_review(mastery, last_review_day, interval_days=None):
    # mastery is expected in [0,1]
    if interval_days is None:
        interval_days=1 if mastery<0.6 else (3 if mastery<0.85 else 7)
    return {"last_review_day":last_review_day,
            "interval_days":interval_days,
            "next_review_day":last_review_day+interval_days}
