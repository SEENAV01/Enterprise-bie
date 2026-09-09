def entry(i,fingerprint,artifacts=None,status="VALID"): return {"node_id":i,"fingerprint":fingerprint,"artifact_refs":artifacts or [],"status":status}
def reusable(e,fingerprint): return e["status"]=="VALID" and e["fingerprint"]==fingerprint
