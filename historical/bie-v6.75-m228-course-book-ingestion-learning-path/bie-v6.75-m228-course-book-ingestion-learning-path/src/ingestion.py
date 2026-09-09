def ingest_outline(source,outline):
    return {"source":source,"chapters":outline.get("chapters",[]),
            "sections":outline.get("sections",[]),
            "metadata":outline.get("metadata",{})}

def validate_structure(doc):
    chapter_ids={c["chapter_id"] for c in doc.get("chapters",[])}
    errors=[]
    for s in doc.get("sections",[]):
        if s.get("chapter_id") not in chapter_ids:
            errors.append("ORPHAN_SECTION:"+s.get("section_id",""))
    return {"passed":not errors,"errors":errors}
