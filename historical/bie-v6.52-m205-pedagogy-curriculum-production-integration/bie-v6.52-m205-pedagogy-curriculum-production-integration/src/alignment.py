def alignment_record(record_id, objective_ids,
                     strategy_ids, assessment_ids, evidence_ids=None):
    return {"record_id": record_id, "objective_ids": objective_ids,
            "strategy_ids": strategy_ids, "assessment_ids": assessment_ids,
            "evidence_ids": evidence_ids or []}

def valid(record):
    return (bool(record["objective_ids"]) and
            bool(record["strategy_ids"]) and
            bool(record["assessment_ids"]))
