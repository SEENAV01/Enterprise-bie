def validate_course(course,lessons,chapters):
    errors=[]
    cids=[c["chapter_id"] for c in chapters]
    lids=[l["lesson_id"] for l in lessons]
    if len(cids)!=len(set(cids)): errors.append("DUPLICATE_CHAPTER_ID")
    if len(lids)!=len(set(lids)): errors.append("DUPLICATE_LESSON_ID")
    known=set(lids)
    for c in chapters:
        for lid in c.get("lesson_ids",[]):
            if lid not in known: errors.append("UNKNOWN_LESSON_REFERENCE")
    return {"valid":not errors,"errors":errors}
