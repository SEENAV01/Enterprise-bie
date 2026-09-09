def saga_definition(steps):
    return {"steps":steps,
            "compensation_order":
                [s["step_id"] for s in reversed(steps)
                 if s.get("compensation")]}

def compensation_plan(steps,completed_step_ids):
    completed=set(completed_step_ids)
    return [s["compensation"] for s in reversed(steps)
            if s["step_id"] in completed and s.get("compensation")]
