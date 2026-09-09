def classify_segment(segment, candidates):
    results=[]
    for i,c in enumerate(candidates,1):
        results.append({
          "id":f'{segment["segment_id"]}_x{i}',
          "segment_id":segment["segment_id"],
          "dimension":c["dimension"],
          "text":c["text"],
          "source_span":c.get("source_span",segment["segment_id"]),
          "confidence":c.get("confidence","CANDIDATE"),
          "evidence_ids":c.get("evidence_ids",[])
        })
    return results
