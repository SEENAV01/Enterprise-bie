class E(ValueError):pass
REQUIRED=("concepts","relations","claims","definitions","examples","terms","entities","conditions")
def run(doc):
 missing=[k for k in REQUIRED if k not in doc]
 if missing:raise E("missing:"+",".join(missing))
 concepts={x["concept_id"] for x in doc["concepts"]}
 bad=[r for r in doc["relations"] if r["source"] not in concepts or r["target"] not in concepts]
 unsupported=[c["claim_id"] for c in doc["claims"] if not c.get("anchor_ids")]
 return {"concept_count":len(concepts),"relation_count":len(doc["relations"]),"unsupported_claims":tuple(unsupported),
 "passed":not bad and not unsupported,"bad_relations":tuple(bad),"stages":REQUIRED}
