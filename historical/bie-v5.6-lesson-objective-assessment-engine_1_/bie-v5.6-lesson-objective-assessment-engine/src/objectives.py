OBJECTIVE_TYPES=["RECALL","EXPLAIN","APPLY","ANALYZE","CREATE","TRANSFER"]

def objective(objective_id, concept_id, statement, level="UNDERSTAND",
              success_criteria=None):
    return {
      "objective_id":objective_id,
      "concept_id":concept_id,
      "statement":statement,
      "level":level,
      "success_criteria":success_criteria or [],
      "measurable":True
    }
