def escalate(confidence,conflict,unsupported,available_routes):
 if not 0<=confidence<=1 or not 0<=conflict<=1:raise ValueError("normalized values")
 routes=set(available_routes)
 if unsupported and "specialist" in routes:return "specialist"
 if conflict>=.6 and "evidence_review" in routes:return "evidence_review"
 if confidence<.45 and "stronger_model" in routes:return "stronger_model"
 return "none"
