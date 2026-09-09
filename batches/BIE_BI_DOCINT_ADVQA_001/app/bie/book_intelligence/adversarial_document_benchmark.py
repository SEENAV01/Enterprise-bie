REQUIRED={"poor_scan","multi_column","dense_math","multilingual","tables","diagrams","footnotes","rotated"}
class E(ValueError):pass
def evaluate(cases,min_score=.9):
 seen={c["category"] for c in cases}; missing=REQUIRED-seen
 if missing:raise E("missing categories:"+",".join(sorted(missing)))
 bad=[c["id"] for c in cases if not 0<=c["score"]<=1]
 if bad:raise E("score")
 avg=sum(c["score"] for c in cases)/len(cases)
 return {"passed":avg>=min_score and all(c["score"]>=.7 for c in cases),"average":avg,"count":len(cases)}
