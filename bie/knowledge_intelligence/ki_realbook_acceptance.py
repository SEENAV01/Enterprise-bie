class E(ValueError):pass
DOMAINS={"PHYSICS","MATHEMATICS","BIOLOGY","HISTORY","GEOGRAPHY"}
def evaluate(cases,min_coverage=.90):
 seen=set();fail=[]
 for c in cases:
  if c.get("domain") not in DOMAINS:raise E("domain")
  seen.add(c["domain"])
  if c.get("concept_coverage",0)<min_coverage or c.get("unsupported_claims",1)>0 or not c.get("graph_valid",False):fail.append(c["case_id"])
 return {"domains_seen":tuple(sorted(seen)),"five_domain_ready":seen==DOMAINS,"failed_cases":tuple(fail),
 "accepted":seen==DOMAINS and not fail}
