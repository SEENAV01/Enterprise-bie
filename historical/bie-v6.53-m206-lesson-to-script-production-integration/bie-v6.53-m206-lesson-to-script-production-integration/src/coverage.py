def coverage(objective_ids, blocks):
    covered={oid:[] for oid in objective_ids}
    for b in blocks:
        for oid in b.get("objective_ids",[]):
            if oid in covered:
                covered[oid].append(b["block_id"])
    return covered

def complete(cov):
    return bool(cov) and all(ids for ids in cov.values())
