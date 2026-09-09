KNOWLEDGE_CLASSES=[
"BOOK_EXPLICIT","BOOK_IMPLIED","PREREQUISITE","APPLICATION",
"HIGHER_KNOWLEDGE","GENERALIZATION","EXTERNAL_CONTEXT"
]
CONFIDENCE_LEVELS=["VERIFIED","SUPPORTED","INFERRED","CANDIDATE","UNVERIFIED"]

def knowledge_item(item_id, title, classification, content,
                   source_refs=None, depends_on=None, confidence="CANDIDATE"):
    return {
      "id":item_id,
      "title":title,
      "classification":classification,
      "content":content,
      "source_refs":source_refs or [],
      "depends_on":depends_on or [],
      "confidence":confidence,
      "allowed_for_teaching":False
    }
