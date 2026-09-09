from deduplication import cluster_duplicates

def reconcile_claims(claims):
    clusters=cluster_duplicates(claims)
    canonical=[]; mappings={}
    for i,cluster in enumerate(clusters,1):
        canonical_id=f"claim_canonical_{i}"
        best=max(cluster,key=lambda x:float(x.get("source_quality",0)))
        canonical.append({
          "id":canonical_id,
          "text":best.get("text",""),
          "members":[x["id"] for x in cluster],
          "evidence_ids":[e for x in cluster for e in x.get("evidence_ids",[])],
          "status":"REQUIRES_REVIEW" if len(cluster)>1 and
                  any(x.get("relation")=="CONTRADICTS" for x in cluster)
                  else "RECONCILED"
        })
        for x in cluster:mappings[x["id"]]=canonical_id
    return canonical,mappings
