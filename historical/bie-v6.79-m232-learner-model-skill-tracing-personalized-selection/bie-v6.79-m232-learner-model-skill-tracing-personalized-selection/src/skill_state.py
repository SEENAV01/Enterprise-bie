def skill_state(skill_id,mastery=0.0,evidence_count=0,
               last_updated=None):
    return {"skill_id":skill_id,"mastery":float(mastery),
            "evidence_count":int(evidence_count),"last_updated":last_updated}

def update_skill(state,score,weight=1.0):
    old=state.get("mastery",0.0); n=state.get("evidence_count",0)
    new=(old*n+score*weight)/(n+weight) if n+weight else old
    return {**state,"mastery":new,"evidence_count":n+weight}
