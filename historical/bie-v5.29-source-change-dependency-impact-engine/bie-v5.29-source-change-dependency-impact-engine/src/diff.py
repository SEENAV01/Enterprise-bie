def content_diff(before,after):
    return {"changed":before!=after,
            "before_length":len(before or ""),
            "after_length":len(after or "")}

def semantic_change(change_type,meaning_changed):
    return {"change_type":change_type,"meaning_changed":meaning_changed,
            "requires_reassessment":bool(meaning_changed)}
