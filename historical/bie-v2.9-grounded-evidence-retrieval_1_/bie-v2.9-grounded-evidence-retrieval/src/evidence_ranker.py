def rank_evidence(results, query):
    def score(e):
        base=e.get("retrieval_score",0)
        modality_bonus={"equation":.10,"table":.08,"image":.06,"text":0}.get(e.get("modality"),0)
        provenance_bonus=.05 if e.get("provenance",{}).get("source")=="BOOK" else 0
        return base+modality_bonus+provenance_bonus
    return sorted(results,key=score,reverse=True)
