def trace_video_element(element_id,element_type,claim_ids,
                       evidence_ids,transformations=None):
    return {
      "element_id":element_id,
      "element_type":element_type,
      "claim_ids":claim_ids,
      "evidence_ids":evidence_ids,
      "transformations":transformations or []
    }

def trace_path(element_id,graph):
    node=graph.get(element_id)
    if not node: return []
    return [node]
