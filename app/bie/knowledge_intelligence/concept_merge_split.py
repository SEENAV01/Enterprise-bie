class E(ValueError):pass
def decide(a,b,label_similarity,evidence_overlap,scope_overlap):
 vals=(label_similarity,evidence_overlap,scope_overlap)
 if any(not 0<=x<=1 for x in vals):raise E("score")
 if a==b:raise E("same concept")
 weighted=.45*label_similarity+.35*evidence_overlap+.20*scope_overlap
 action="MERGE" if weighted>=.85 else ("REVIEW" if weighted>=.65 else "KEEP_SEPARATE")
 return {"left":a,"right":b,"score":weighted,"action":action,"requires_evidence":True}
def split(concept_id,subconcepts):
 vals=tuple(dict.fromkeys(x.strip() for x in subconcepts if x.strip()))
 if not concept_id or len(vals)<2:raise E("split")
 return {"concept_id":concept_id,"action":"SPLIT_REVIEW","subconcepts":vals}
