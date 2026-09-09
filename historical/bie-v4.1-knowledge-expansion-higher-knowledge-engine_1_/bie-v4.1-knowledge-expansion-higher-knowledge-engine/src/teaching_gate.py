def teaching_gate(item):
    if item["classification"] in ["BOOK_EXPLICIT","BOOK_IMPLIED","PREREQUISITE"]:
        return {"allowed":item["confidence"] in ["VERIFIED","SUPPORTED"],
                "reason":"book-grounded"}
    if item["classification"] in ["HIGHER_KNOWLEDGE","GENERALIZATION","APPLICATION","EXTERNAL_CONTEXT"]:
        return {"allowed":item["confidence"]=="VERIFIED" and bool(item.get("source_refs")),
                "reason":"external-evidence-required"}
    return {"allowed":False,"reason":"unknown-classification"}
