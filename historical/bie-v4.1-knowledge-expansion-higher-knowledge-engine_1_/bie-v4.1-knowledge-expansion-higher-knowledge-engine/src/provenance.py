def provenance_record(item, book_refs=None, external_refs=None, inference=None):
    return {
      "knowledge_id":item["id"],
      "book_refs":book_refs or item.get("source_refs",[]),
      "external_refs":external_refs or [],
      "inference":inference,
      "separation":{
        "book_derived":bool(book_refs or item.get("source_refs")),
        "externally_verified":bool(external_refs),
        "model_inference":inference is not None
      }
    }

def provenance_gate(item, record):
    if item["classification"] in ["HIGHER_KNOWLEDGE","EXTERNAL_CONTEXT","GENERALIZATION"]:
        return bool(record.get("external_refs")) and item["confidence"]=="VERIFIED"
    return True
