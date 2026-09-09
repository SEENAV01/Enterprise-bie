def evidence_binding(asset_id, evidence_ids=None,
                    source_record_ids=None, verification_ids=None):
    return {
        "asset_id": asset_id,
        "evidence_ids": evidence_ids or [],
        "source_record_ids": source_record_ids or [],
        "verification_ids": verification_ids or []
    }

def grounded(item):
    return bool(item["evidence_ids"] or item["source_record_ids"])
