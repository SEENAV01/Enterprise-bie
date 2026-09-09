def cross_modal_link(link_id, source_id, record_ids,
                    relation, confidence=1.0):
    if len(record_ids) < 2:
        raise ValueError("CROSS_MODAL_LINK_REQUIRES_TWO_RECORDS")
    return {
        "link_id": link_id, "source_id": source_id,
        "record_ids": record_ids, "relation": relation,
        "confidence": confidence
    }

def valid(record):
    return len(record["record_ids"]) >= 2 and bool(record["relation"])
