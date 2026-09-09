OBJECTIVE_TYPES=[
"UNDERSTAND","EXPLAIN","RECALL","DISTINGUISH","APPLY",
"CALCULATE","DERIVE","PREDICT","ANALYZE","EVALUATE","CREATE"
]
def objective(obj_id, statement, obj_type, evidence_ids=None):
    return {"id":obj_id,"statement":statement,"type":obj_type,
            "evidence_ids":evidence_ids or []}
