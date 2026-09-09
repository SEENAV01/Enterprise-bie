def review_required(confidence,evidence_coverage,conflict,threshold=.60):
 if any(v<0 or v>1 for v in (confidence,evidence_coverage,conflict,threshold)):raise ValueError("normalized values required")
 effective=confidence*evidence_coverage*(1-.5*conflict)
 return {"review":effective<threshold,"effective_confidence":effective,"threshold":threshold}
