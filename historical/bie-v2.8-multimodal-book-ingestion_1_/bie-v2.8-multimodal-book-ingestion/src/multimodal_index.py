def build_index(book):
    index={"text":[],"image":[],"table":[],"equation":[]}
    for e in book["evidence"]:
        if e["modality"] in index:
            index[e["modality"]].append(e["evidence_id"])
    return index
