def provenance(batch,course,nodes,changed_nodes,rebuilt_nodes,artifacts=None): return {"batch_id":batch,"course_ref":course,"node_ids":nodes,"changed_node_ids":changed_nodes,"rebuilt_node_ids":rebuilt_nodes,"artifact_ids":artifacts or []}
def traceable(p): return bool(p["batch_id"] and p["course_ref"] and p["node_ids"])
