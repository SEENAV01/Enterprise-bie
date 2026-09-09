def update_mastery(old_mastery,score,weight=0.2):
    old=0.0 if old_mastery is None else old_mastery
    if score is None: return old
    return max(0.0,min(1.0,old+weight*(score-old)))

def mastery_state(concept_id,mastery,attempts=0,correct=0):
    return {"concept_id":concept_id,"mastery":mastery,
            "attempts":attempts,"correct":correct}
