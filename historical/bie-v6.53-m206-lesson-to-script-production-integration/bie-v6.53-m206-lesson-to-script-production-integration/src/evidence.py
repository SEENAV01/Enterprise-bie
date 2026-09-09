def evidence_check(blocks):
    return [
        {"block_id":b["block_id"],
         "grounded":bool(b.get("evidence_ids")),
         "evidence_ids":b.get("evidence_ids",[])}
        for b in blocks
    ]

def all_grounded(checks):
    return all(x["grounded"] for x in checks)
