def calendar(calendar_id, timezone="UTC",
            business_days=None, holidays=None):
    return {"calendar_id":calendar_id,"timezone":timezone,
            "business_days":business_days or [],
            "holidays":holidays or []}

def holiday(record, date):
    return date in record["holidays"]
