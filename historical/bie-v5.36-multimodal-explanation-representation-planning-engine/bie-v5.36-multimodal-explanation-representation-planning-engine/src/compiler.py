from cognitive_load import cognitive_load_budget,multimodal_overlap_guard
from selection import rank_representations
from synchronization import sync_plan

def compile_multimodal_plan(units,representations,signals=None,
                            sync_items=None,load_budgets=None):
    rep_ids={r["rep_id"] for r in representations}
    plans=[]
    errors=[]
    for u in units:
        refs=[r for r in representations
              if r["rep_id"] in u.get("representation_refs",[])]
        missing=[x for x in u.get("representation_refs",[]) if x not in rep_ids]
        if missing: errors.append("MISSING_REPRESENTATION_REFERENCE")
        ranked=rank_representations(refs,signals)
        plans.append({"unit_id":u["unit_id"],
                      "ranked_representations":ranked,
                      "overlap_guard":multimodal_overlap_guard(ranked)})
    budgets=[cognitive_load_budget(**b) for b in (load_budgets or [])]
    if any(not x["within_budget"] for x in budgets):
        errors.append("COGNITIVE_LOAD_BUDGET_EXCEEDED")
    return {"schema_version":"5.36",
            "plans":plans,"sync_plan":sync_plan(sync_items or []),
            "load_budgets":budgets,
            "quality_gate":{"valid":not errors,"errors":errors}}
