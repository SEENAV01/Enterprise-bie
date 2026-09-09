def retention_policy(name,retain_released=True,
                     retain_days=None,protect_refs=True):
    return {"name":name,"retain_released":retain_released,
            "retain_days":retain_days,
            "protect_refs":protect_refs}

def gc_eligible(record,policy,referenced=False):
    if policy.get("protect_refs",True) and referenced:
        return False
    if record.get("state") not in {"ARCHIVED","GC_ELIGIBLE"}:
        return False
    return True
