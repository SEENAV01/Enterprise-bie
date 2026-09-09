def next_action(mastery, prerequisite_ready=True):
    if not prerequisite_ready:
        return "TEACH_PREREQUISITE"
    if mastery<0.50:
        return "RETEACH_WITH_ALTERNATE_EXPLANATION"
    if mastery<0.70:
        return "PRACTICE"
    if mastery<0.85:
        return "TRANSFER_PRACTICE"
    return "ADVANCE"
