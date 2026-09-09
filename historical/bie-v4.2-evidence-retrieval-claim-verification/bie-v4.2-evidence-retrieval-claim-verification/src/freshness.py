def freshness_check(source, relevant_year=None):
    if relevant_year is None:
        return {"status":"NOT_REQUIRED","reason":"NO_TIME_SENSITIVE_CONTEXT"}
    published=source.get("published")
    if not published:
        return {"status":"UNKNOWN","reason":"NO_PUBLICATION_DATE"}
    try:
        year=int(str(published)[:4])
    except Exception:
        return {"status":"UNKNOWN","reason":"UNPARSEABLE_DATE"}
    return {"status":"CURRENT_OR_RELEVANT" if year>=relevant_year else "OLDER_SOURCE",
            "published_year":year,"required_year":relevant_year}
