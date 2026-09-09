def scene_coverage(objective_ids, scenes):
    covered={oid:[] for oid in objective_ids}
    for s in scenes:
        for oid in s.get("objective_ids",[]):
            if oid in covered:
                covered[oid].append(s["scene_id"])
    return covered

def complete(coverage):
    return bool(coverage) and all(ids for ids in coverage.values())
