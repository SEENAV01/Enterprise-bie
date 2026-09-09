def collect_candidates(records,policy,reference_set=None):
    refs=set(reference_set or [])
    return [r for r in records
            if r.get("artifact_id") not in refs
            and r.get("state") in {"ARCHIVED","GC_ELIGIBLE"}]

def deletion_plan(records,policy,reference_set=None):
    return [r["artifact_id"]
            for r in collect_candidates(records,policy,reference_set)]
