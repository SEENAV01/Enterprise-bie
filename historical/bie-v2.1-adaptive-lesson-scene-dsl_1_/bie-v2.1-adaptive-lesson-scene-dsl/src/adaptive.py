def choose_action(mastery, prerequisite_ok=True):
    if not prerequisite_ok:
        return "TEACH_PREREQUISITE"
    if mastery < .60:
        return "RETEACH"
    if mastery < .80:
        return "PRACTICE"
    if mastery < .90:
        return "APPLY"
    return "ADVANCE"

def branch(unit, mastery, prerequisite_ok=True):
    return {
        "unit_id":unit["unit_id"],
        "mastery":mastery,
        "action":choose_action(mastery,prerequisite_ok),
        "skip_if_mastered":mastery>=.90
    }
