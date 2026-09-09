def reveal_policy(mastered=False,requested=False,hint_level="CONCEPT",max_level="PARTIAL_SOLUTION"):
    if mastered or requested:
        return {"allowed":True,"level":"FULL_SOLUTION","reason":"mastery_or_explicit_request"}
    allowed=LEVELS.index(hint_level)<=LEVELS.index(max_level)
    return {"allowed":allowed,"level":hint_level,
            "reason":"scaffolded_progression" if allowed else "answer_reveal_blocked"}

LEVELS=["CONCEPT","STRATEGY","STEP","PARTIAL_SOLUTION","FULL_SOLUTION"]
