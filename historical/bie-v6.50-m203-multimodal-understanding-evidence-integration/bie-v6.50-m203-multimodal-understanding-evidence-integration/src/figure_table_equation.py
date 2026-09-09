def structured_object(object_id, source_id, kind,
                     record_ids, semantic_label=None):
    if kind not in {"FIGURE", "TABLE", "EQUATION"}:
        raise ValueError("INVALID_STRUCTURED_OBJECT")
    return {
        "object_id": object_id, "source_id": source_id,
        "kind": kind, "record_ids": record_ids,
        "semantic_label": semantic_label
    }

def complete(record):
    return bool(record["record_ids"]) and bool(record["semantic_label"])
