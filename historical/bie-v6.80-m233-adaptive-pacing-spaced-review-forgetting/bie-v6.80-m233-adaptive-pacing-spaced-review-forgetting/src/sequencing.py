def sequence_lessons(lessons,masteries,review_risks=None):
    review_risks=review_risks or {}
    def score(l):
        skills=l.get("skill_ids",[])
        mastery=sum(masteries.get(s,0) for s in skills)/len(skills) if skills else 1
        risk=max([review_risks.get(s,0) for s in skills] or [0])
        return (1-mastery)+risk
    return sorted(lessons,key=score,reverse=True)

def session_plan(lessons,masteries,pace_info):
    return {"ordered_lessons":sequence_lessons(lessons,masteries),
            "recommended_minutes":pace_info["recommended_minutes"]}
