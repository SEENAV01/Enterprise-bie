def candidate_set(actions,source_refs=None):
    return {"actions":actions,"source_refs":source_refs or []}

def filter_candidates(actions,available_refs=None):
    if available_refs is None:
        return actions
    available=set(available_refs)
    return [a for a in actions
            if not a.get("target_refs") or
            any(x in available for x in a["target_refs"])]
