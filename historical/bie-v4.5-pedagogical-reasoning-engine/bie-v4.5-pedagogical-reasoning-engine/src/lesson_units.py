def make_teaching_unit(item, strategy):
    return {
      "unit_id":"unit_"+item["id"],
      "knowledge_id":item["id"],
      "importance":item.get("importance_class","SUPPORTING"),
      "objective_ids":item.get("objective_ids",[]),
      "teaching_mode":strategy["mode"],
      "source_spans":item.get("source_spans",[]),
      "prerequisites":item.get("prerequisites",[]),
      "assessment_hooks":[
        "CHECK_RECALL" if strategy["mode"]=="EXPLAIN" else "CHECK_APPLICATION"
      ]
    }
