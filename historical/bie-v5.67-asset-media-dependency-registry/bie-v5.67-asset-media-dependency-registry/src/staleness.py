def impacted_assets(reg,changed_keys):
    impacted=set(changed_keys)
    changed=True
    while changed:
        changed=False
        for r in reg.get("relations",[]):
            if r.get("source") in impacted and r.get("target") not in impacted:
                impacted.add(r["target"]); changed=True
    return sorted(impacted)

def stale_consumers(reg,changed_keys):
    return impacted_assets(reg,changed_keys)
