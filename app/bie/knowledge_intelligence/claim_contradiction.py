class E(ValueError):pass
def detect(a,b):
 if not a.get("claim_id") or not b.get("claim_id"):raise E("claim")
 same=a.get("subject")==b.get("subject") and a.get("predicate")==b.get("predicate")
 conflict=same and a.get("object")!=b.get("object")
 return {"contradiction":conflict,"status":"REVIEW" if conflict else "CLEAR","claims":(a["claim_id"],b["claim_id"])}
