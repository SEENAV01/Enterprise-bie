from routing import select_action,route_correction

def correction_plan(diagnosis,causes):
    layer=route_correction(diagnosis,causes)
    action=select_action(diagnosis,causes)
    return {"diagnosis_id":diagnosis.get("diagnosis_id"),
            "target_layer":layer,"action_type":action,
            "cause_candidates":causes}

def next_iteration(previous_result,diagnosis,causes):
    plan=correction_plan(diagnosis,causes)
    return {"previous_result":previous_result,
            "correction_plan":plan,
            "requires_revalidation":plan["action_type"] not in ["NO_ACTION"]}
