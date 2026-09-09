from knowledge_types import knowledge_item

def classify_candidate(candidate):
    relation=candidate.get("relation","")
    mapping={
      "explicit":"BOOK_EXPLICIT",
      "implied":"BOOK_IMPLIED",
      "prerequisite":"PREREQUISITE",
      "application":"APPLICATION",
      "extends":"HIGHER_KNOWLEDGE",
      "generalizes":"GENERALIZATION",
      "external":"EXTERNAL_CONTEXT"
    }
    return mapping.get(relation,"EXTERNAL_CONTEXT")

def create_candidates(book_concepts, candidates):
    out=[]
    for i,c in enumerate(candidates,1):
        cls=classify_candidate(c)
        confidence="CANDIDATE"
        if c.get("verified"): confidence="VERIFIED"
        elif c.get("supported_by_book"): confidence="SUPPORTED"
        out.append(knowledge_item(
          c.get("id",f"candidate_{i}"),
          c["title"],cls,c.get("content",""),
          c.get("source_refs",[]),c.get("depends_on",[]),confidence
        ))
    return out
